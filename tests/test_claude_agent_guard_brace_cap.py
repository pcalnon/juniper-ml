#!/usr/bin/env python3
"""The agent guard expands brace words as bash does, at most 64 alternatives, and refuses what it cannot.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``util/claude_agent_guard.py`` expands ``{a,b}`` and ``{1..3}`` so a credential
name hidden in the last alternative is still seen. The expansion is capped at
``MAX_BRACE_ALTERNATIVES`` (64): the last slot of a full list is kept and judged.
A word that needs more alternatives is refused (``MalformedInput``, which the hook
turns into exit 2) instead of being judged on its first 64: the owner's
"Fail closed" ruling of 2026-11-08. Until then alternative 65 was dropped, so a
``.ssh`` or ``.gnupg`` spelled there passed the credential check.

The cap still bounds the work. A list is counted part by part, so at most one
part past the cap is taken in (a nested part adds at most 64 words), and a numeric
or letter range is sized arithmetically inside ``_brace_range``, which applies the
cap even when ``brace_expand`` is asked for a higher limit, so ``{1..1000000}`` is
refused without materializing a million strings. A product of small groups counts
as its product, and a stepped sequence counts its terms.

The scan is bounded too. bash looks for the ``}`` of each ``{`` by scanning to the
end of the word, the square of the word's length when most groups never close:
ported as written, the hook took 7.7 s on a 25.8 KB ``python3 -c`` word, and its
timeout is 10 s. ``_brace_closes`` answers every ``{`` of a word in one pass, and
``BRACE_SCAN_BUDGET`` bounds what nested lists add, since each list part is scanned
again when it is expanded: a word that needs more is refused, never passed
unexamined. A word with no ``{`` is not scanned at all.

Sequence expressions (owner ruling "Carry in ml-code", 2026-11-09). bash 4+ also
expands ``{x..y..incr}``, which the guard left as written, so
``cat ~/.{r..t..1}sh/config`` read ``~/.ssh/config`` past the credential check.
The guard now follows bash 5.3's own brace code: a step of either sign, a step of
0, a step past the range, ``+`` signs, zero padding (``{01..03}``, which it had
expanded as ``1 2 3``), a ``}`` before the first separator kept as text, and no
rescan of the words one expansion made. It refuses what it does not model: a
sequence group with a brace inside it (bash 5.2 and 5.3 make different words of
``{a..{c,d}}``), a letter sequence that makes a backslash or a backtick (bash reads
them as an escape and a command substitution), and an operand past 2**61.
``SEQUENCE_CASES`` holds the words bash 5.3.9 made of each source word
(``util/ad-hoc/2026-11-08_flood4r2_ml_code_brace_sequence_probe.py``, 2026-11-09;
every row again, with five separator rows added then, by
``util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_pins_vs_bash.py`` on 2026-11-11).
The tests do not run bash: macOS's /bin/bash 3.2 has neither steps nor padding.

The source words under test do not contain the text ``.ssh`` or ``.gnupg``. The
raw-command regex therefore cannot be what denies them; a deny comes from an
expanded alternative, and a refusal from the cap or from a sequence the guard
does not model.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "util" / "claude_agent_guard.py"
LARGE_COUNTS = (10_000, 100_000)


def _load_guard():
    spec = importlib.util.spec_from_file_location("claude_agent_guard_brace_cap", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assembled_at(alternative_count: int, head: str, tail: str) -> str:
    """``alternative_count`` alternatives; the last is ``head`` and the word ends in ``tail``."""
    fillers = [f"n{index}" for index in range(alternative_count - 1)]
    return "{" + ",".join(fillers + [head]) + "}" + tail


def _ssh_assembled_at(alternative_count: int) -> str:
    """The last alternative expands to ``.ssh``; the source does not contain it."""
    return _assembled_at(alternative_count, ".ss", "h")


def _gnupg_assembled_at(alternative_count: int) -> str:
    """The last alternative expands to ``.gnupg``; the source does not contain it."""
    return _assembled_at(alternative_count, ".gnu", "pg")


# (source word, the words bash 5.3.9 made of it, in its order): the guard must make exactly these.
SEQUENCE_CASES = [
    ("{a..e..2}", ["a", "c", "e"]),
    ("{e..a..2}", ["e", "c", "a"]),
    ("{a..e..-2}", ["a", "c", "e"]),  # the step's sign is ignored: the two ends give the direction
    ("{e..a..-2}", ["e", "c", "a"]),
    ("{a..e..0}", ["a", "b", "c", "d", "e"]),  # a step of 0 counts as 1
    ("{a..e..10}", ["a"]),  # a step past the range leaves the first end alone
    ("{r..t..1}", ["r", "s", "t"]),
    ("{1..10..3}", ["1", "4", "7", "10"]),
    ("{10..1..-3}", ["10", "7", "4", "1"]),
    ("{1..5..-0}", ["1", "2", "3", "4", "5"]),
    ("{5..1..-10}", ["5"]),
    ("{+1..+3}", ["1", "2", "3"]),
    ("{01..03}", ["01", "02", "03"]),  # zero padding: the guard used to make 1 2 3
    ("{1..010..3}", ["001", "004", "007", "010"]),
    ("{-01..3}", ["-01", "000", "001", "002", "003"]),
    ("{+1..03}", ["01", "02", "03"]),
    ("{-0..3}", ["0", "1", "2", "3"]),  # -0 alone pads nothing
    ("{01..10..3}", ["01", "04", "07", "10"]),
    ("{1..10..03}", ["1", "4", "7", "10"]),  # a padded step pads nothing
    ("{Y..a..2}", ["Y", "[", "]", "_", "a"]),  # from Z to a, but no backslash and no backtick
    ("{a..e..2}x{1..2}", ["ax1", "ax2", "cx1", "cx2", "ex1", "ex2"]),
    ("{{a..c},d}", ["a", "b", "c", "d"]),
    ("{a,{1..3..1}}", ["a", "1", "2", "3"]),
    ("{x{a..c}}", ["{xa}", "{xb}", "{xc}"]),
    ("{x{.,a}.y}", ["{x..y}", "{xa.y}"]),  # bash does not rescan the {x..y} it made
    ("{a}b,c}", ["a}b", "c"]),  # a top-level } before the first separator stays as text
    ("{a..c,d}", ["a..c", "d"]),  # a comma wins over an earlier ..: a list, not a sequence
    ("{a.bc}d,e}", ["a.bc}d", "e"]),  # one . is no separator, so the first } is text
    ("{a..}b,c}", ["a..}b", "c"]),  # nor is a .. directly before a }
    ("{a..c}d,e}", ["ad,e}", "bd,e}", "cd,e}"]),  # the sequence closes at its own }: the comma after it is outside
    ("{a..{b}c,d}", ["a..{b}c", "d"]),  # a comma after a nested {b} still wins over the .. before it
    ("{a..1}{x,y}", ["{a..1}x", "{a..1}y"]),  # not a sequence: kept as written, braces and all
    ("{1..2..x}", ["{1..2..x}"]),
    ("{1..9223372036854775808}", ["{1..9223372036854775808}"]),  # past intmax_t bash keeps it as written
    ("{2305843009213693952..2305843009213693952}", ["2305843009213693952"]),  # 2**61, the largest operand modelled
]
# (source word, the reason the guard gives): what the guard refuses rather than model.
REFUSED_SEQUENCES = [
    ("{a..{c,d}}", "with a brace inside it"),  # bash 5.3: {a..c} {a..d}; bash 5.2: a..c a..d
    ("{{a..c}..e}", "with a brace inside it"),
    ("{1..3{,}}", "with a brace inside it"),
    ("x{{a,b}..c}", "with a brace inside it"),
    ("{Z..a}", "a backslash or a backtick"),
    (".ss{Y..a..3}h", "a backslash or a backtick"),  # bash: .ssYh .ssh .ss_h, its backslash escaping the h
    ("{Z..a..3}", "a backslash or a backtick"),  # Z, ] and a backtick: no backslash
    ("{2305843009213693953..2305843009213693953}", r"beyond 2\*\*61"),
    ("{1..9223372036854775807}", r"beyond 2\*\*61"),  # intmax_t itself is still a number to bash: refused, not kept as written
]
# (command, the rule it must trip): a sequence that assembles a guarded name.
SEQUENCE_DENIES = [
    ("cat ~/.{r..t..1}sh/config", "CRED-PATH-BASH"),  # the bypass: .rsh .ssh .tsh
    ("ls ~/.{f..h..1}nupg", "CRED-PATH-BASH"),
    ("cat ~/.{t..r..-1}sh/config", "CRED-PATH-BASH"),
    ("cat ~/.{q..u..2}sh/config", "CRED-PATH-BASH"),  # q s u: the step lands on s
    ("cat ~/.ss{h..h..0}/config", "CRED-PATH-BASH"),
    ("cat ~/.ss{x..y,h}/config", "CRED-PATH-BASH"),  # a list whose first part holds a ..: bash makes .ssx..y and .ssh
    ("{s..s..1}udo true", "PRIV-ESCALATION"),
    ("gpg{2..2..1} --card-status", "GPG-SECRET"),
]


class GuardBraceHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = _load_guard()
        self.assertEqual(self.guard.MAX_BRACE_ALTERNATIVES, 64)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name) / "home"
        for name in (".ssh", ".gnupg", ".claude"):
            (self.home / name).mkdir(parents=True)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self.ctx = self.guard.Context([str(self.home)], str(self.repo))

    def analyze(self, command: str) -> list:
        """A fresh analyzer per command: one accumulates hits across calls."""
        return self.guard.BashAnalyzer(self.ctx).analyze(command)

    def _hook(self, tool: str, tool_input: dict) -> tuple:
        payload = json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(self.repo)}).encode("utf-8")
        return self.guard.run_hook(payload, homes=[str(self.home)], project_dir=str(self.repo))

    def assert_refused_by_the_cap(self, tool: str, tool_input: dict) -> None:
        self.assert_refused(tool, tool_input, "more than 64 alternatives")

    def assert_refused(self, tool: str, tool_input: dict, reason: str) -> None:
        code, out, err = self._hook(tool, tool_input)
        self.assertEqual((code, out), (2, ""), "a word the guard cannot analyse must fail closed: exit 2, nothing on stdout")
        self.assertIn("fail closed", err)
        self.assertIn(reason, err)


class BraceExpansionCapTest(GuardBraceHarness):

    def test_last_slot_of_a_full_list_assembles_ssh_and_is_denied(self) -> None:
        word = _ssh_assembled_at(self.guard.MAX_BRACE_ALTERNATIVES)
        self.assertNotIn(".ssh", word)
        expanded = self.guard.brace_expand(word)
        self.assertIn(".ssh", expanded)
        self.assertIn("n0h", expanded)
        self.assertEqual(len(expanded), self.guard.MAX_BRACE_ALTERNATIVES + 1)  # the word itself, then its 64 alternatives
        hits = self.analyze("echo " + word)
        self.assertIn("CRED-PATH-BASH", [hit.rule_id for hit in hits])

    def test_last_slot_of_a_full_list_assembles_gnupg_and_is_denied(self) -> None:
        word = _gnupg_assembled_at(self.guard.MAX_BRACE_ALTERNATIVES)
        self.assertNotIn(".gnupg", word)
        self.assertIn(".gnupg", self.guard.brace_expand(word))
        hits = self.analyze("ls ~/" + word)
        self.assertIn("CRED-PATH-BASH", [hit.rule_id for hit in hits])

    def test_one_past_the_cap_is_refused(self) -> None:
        """65 alternatives, and far more, fail closed: the analyzer raises instead of judging the first 64."""
        for build in (_ssh_assembled_at, _gnupg_assembled_at):
            for count in (self.guard.MAX_BRACE_ALTERNATIVES + 1,) + LARGE_COUNTS:
                with self.subTest(word=build.__name__, alternatives=count):
                    word = build(count)
                    self.assertNotIn(".ssh", word)
                    self.assertNotIn(".gnupg", word)
                    with self.assertRaisesRegex(self.guard.MalformedInput, "more than 64 alternatives"):
                        self.guard.brace_expand(word)
                    with self.assertRaises(self.guard.MalformedInput):
                        self.analyze("cat ~/" + word + "/config")

    def test_the_hook_fails_closed_past_the_cap(self) -> None:
        """End to end: exit 2 with an empty stdout, for the Bash rules, a Glob or Grep pattern, and a Serena glob."""
        for count in (self.guard.MAX_BRACE_ALTERNATIVES + 1, LARGE_COUNTS[-1]):
            with self.subTest(alternatives=count):
                self.assert_refused_by_the_cap("Bash", {"command": "cat ~/" + _ssh_assembled_at(count) + "/config"})
                self.assert_refused_by_the_cap("Bash", {"command": "ls ~/" + _gnupg_assembled_at(count)})
                self.assert_refused_by_the_cap("Glob", {"pattern": "~/" + _ssh_assembled_at(count) + "/*"})
                self.assert_refused_by_the_cap("Grep", {"pattern": "Host", "path": str(self.repo), "glob": _gnupg_assembled_at(count) + "/*"})
                self.assert_refused_by_the_cap("mcp__serena__replace_in_files", {"paths_include_glob": "**/" + _ssh_assembled_at(count) + "/*", "needle": "a", "repl": "b"})

    def test_a_product_of_small_groups_counts_as_its_product(self) -> None:
        """Six ``{a,b}`` groups make exactly 64 words and are judged; a seventh makes 128 and is refused."""
        at_cap = "{a,b}" * 6
        expanded = self.guard.brace_expand(at_cap)
        self.assertEqual(len(expanded), 64 + 1)
        self.assertEqual(self.analyze("echo " + at_cap), [])
        with self.assertRaises(self.guard.MalformedInput):
            self.guard.brace_expand(at_cap + "{a,b}")
        with self.assertRaises(self.guard.MalformedInput):
            self.analyze("echo {1..8}{1..8}{x,y}")

    def test_numeric_range_of_exactly_the_cap_includes_both_ends(self) -> None:
        cap = self.guard.MAX_BRACE_ALTERNATIVES
        ascending = self.guard._brace_range("1", str(cap))
        self.assertEqual(ascending[0], "1")
        self.assertEqual(ascending[-1], str(cap))
        self.assertEqual(len(ascending), cap)
        descending = self.guard._brace_range(str(cap), "1")
        self.assertEqual(descending[0], str(cap))
        self.assertEqual(descending[-1], "1")
        self.assertEqual(len(descending), cap)
        # The range cap holds even when the outer expander is asked for more.
        wide = self.guard.brace_expand("{1.." + str(cap) + "}", limit=cap * 2)
        self.assertIn("1", wide)
        self.assertIn(str(cap), wide)

    def test_numeric_range_one_past_the_cap_is_refused(self) -> None:
        """Past the cap a range is refused, in either direction, at any outer limit, without being built."""
        cap = self.guard.MAX_BRACE_ALTERNATIVES
        for lo, hi in (("1", str(cap + 1)), (str(cap + 1), "1"), ("0", str(cap)), ("-1", str(cap - 1)), ("1", "1000000000000")):
            with self.subTest(range=f"{{{lo}..{hi}}}"):
                with self.assertRaisesRegex(self.guard.MalformedInput, "more than 64 alternatives"):
                    self.guard._brace_range(lo, hi)
                with self.assertRaises(self.guard.MalformedInput):
                    self.guard.brace_expand("{" + lo + ".." + hi + "}", limit=cap * 2)
        with self.assertRaises(self.guard.MalformedInput):
            self.analyze("for i in {1..100}; do echo $i; done")
        self.assertEqual(self.analyze("for i in $(seq 1 100); do echo $i; done"), [])

    def test_a_list_counts_the_words_its_parts_make(self) -> None:
        """64 parts, the last a two-word list: 65 words, refused."""
        word = "{" + ",".join(f"n{index}" for index in range(63)) + ",{x,y}}"
        with self.assertRaisesRegex(self.guard.MalformedInput, "more than 64 alternatives"):
            self.guard.brace_expand(word)

    def test_deep_nesting_is_refused_not_a_crash(self) -> None:
        """Every nested list adds a word, so 2000 levels are past the cap: refused before the recursion runs out."""
        word = "{a," * 2000 + "b" + "}" * 2000
        with self.assertRaisesRegex(self.guard.MalformedInput, "more than 64 alternatives"):
            self.guard.brace_expand(word)


class BraceSequenceTest(GuardBraceHarness):
    def test_sequences_make_the_words_bash_makes(self) -> None:
        for word, expected in SEQUENCE_CASES:
            with self.subTest(word=word):
                self.assertEqual(self.guard.brace_expand(word), [word] + [w for w in expected if w != word])

    def test_a_sequence_that_assembles_a_guarded_name_is_denied(self) -> None:
        for command, rule in SEQUENCE_DENIES:
            with self.subTest(command=command):
                self.assertNotIn(".ssh", command)
                self.assertNotIn(".gnupg", command)
                self.assertIn(rule, [hit.rule_id for hit in self.analyze(command)])

    def test_the_hook_denies_the_increment_range_bypass(self) -> None:
        code, out, err = self._hook("Bash", {"command": "cat ~/.{r..t..1}sh/config"})
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("CRED-PATH-BASH", out)

    def test_sequences_that_make_no_guarded_name_pass(self) -> None:
        for command in ("echo {01..03} {a..e..2} {10..1..-3}", "for i in {1..64..1}; do echo $i; done", "ls ~/Development/{a..c..1}"):
            with self.subTest(command=command):
                self.assertEqual(self.analyze(command), [])

    def test_sequences_the_guard_does_not_model_are_refused(self) -> None:
        for word, reason in REFUSED_SEQUENCES:
            with self.subTest(word=word):
                self.assertNotIn(".ssh", word)
                with self.assertRaisesRegex(self.guard.MalformedInput, reason):
                    self.guard.brace_expand(word)
                self.assert_refused("Bash", {"command": "cat ~/" + word + "/config"}, "cannot be analysed")

    def test_a_brace_after_a_dollar_opens_no_group(self) -> None:
        """``${...}`` is a parameter expansion to bash. Its ``{`` opens no group here, the braces inside it are
        still searched, and a ``${`` inside a sequence group is no brace: the group is kept, not refused."""
        self.assertEqual(self.guard.brace_expand("${a,b}"), ["${a,b}"])
        self.assertEqual(self.guard.brace_expand("x${a,b}{c,d}"), ["x${a,b}{c,d}", "x${a,b}c", "x${a,b}d"])
        self.assertEqual(self.guard.brace_expand("${x:-{a,b}}"), ["${x:-{a,b}}", "${x:-a}", "${x:-b}"])
        self.assertEqual(self.guard.brace_expand("{1..${n}}"), ["{1..${n}}"])
        self.assertEqual(self.analyze("for i in {1..${n}}; do echo $i; done"), [])

    def test_a_stepped_sequence_counts_its_terms_against_the_cap(self) -> None:
        at_cap = self.guard.brace_expand("{1..640..10}")
        self.assertEqual(len(at_cap), 64 + 1)
        self.assertEqual((at_cap[1], at_cap[-1]), ("1", "631"))
        for word in ("{1..650..10}", "{a..z..1}{1..3}"):
            with self.subTest(word=word):
                with self.assertRaisesRegex(self.guard.MalformedInput, "more than 64 alternatives"):
                    self.guard.brace_expand(word)


def _scan_from_one_brace(text: str, j: int):
    """bash's brace_gobbler, as first ported: one scan from just after a ``{``, to the end of the word when the
    group does not close. (index of the closing ``}``, ``","`` or ``".."``), or None. The oracle for
    ``_brace_closes``, which answers every ``{`` of a word in one pass."""
    depth = 0
    kind = None
    while j < len(text):
        ch = text[j]
        if ch == "}" and depth == 0 and kind is not None:
            return j, kind
        if ch == "{":
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
        elif ch == "," and depth == 0:
            kind = ","
        elif ch == "." and depth == 0 and kind is None and text[j + 1 : j + 2] == "." and text[j + 2 : j + 3] != "}":
            kind = ".."
        j += 1
    return None


class BraceScanTest(GuardBraceHarness):
    """The scan takes one pass per word, and ``BRACE_SCAN_BUDGET`` refuses what nesting would multiply."""

    SMALL_BUDGET = 1000

    def test_the_one_pass_scan_agrees_with_a_scan_from_each_brace(self) -> None:
        """Every word of up to 7 characters over ``{ } , . a`` (97,656 words), and every ``{`` in each."""
        wrong: list = []
        for length in range(8):
            for letters in itertools.product("{},.a", repeat=length):
                text = "".join(letters)
                closes = self.guard._brace_closes(text)
                self.assertEqual(sorted(closes), [i for i, ch in enumerate(text) if ch == "{"])
                wrong += [(text, i) for i in closes if closes[i] != _scan_from_one_brace(text, i + 1)]
        self.assertEqual(wrong[:5], [])

    def test_a_long_word_whose_groups_never_close_passes_and_is_charged_once(self) -> None:
        """25.8 KB of ``v0={x0};v1={x1};...``: no separator, so no group. The hook took 7.7 s on it."""
        word = "".join("v%d={x%d};" % (k, k) for k in range(2000))
        budget = [self.guard.BRACE_SCAN_BUDGET]
        self.assertEqual(self.guard._brace_words(word, self.guard.MAX_BRACE_ALTERNATIVES, word, 0, budget), [word])
        self.assertEqual(self.guard.BRACE_SCAN_BUDGET - budget[0], len(word))  # its length, whatever the number of braces
        self.assertEqual(self.guard.brace_expand(word), [word])
        self.assertEqual(self._hook("Bash", {"command": 'python3 -c "%s"' % word}), (0, "", ""))

    def test_the_scan_takes_time_in_proportion_to_the_word(self) -> None:
        """16,000 braces that open no group. One pass answers them all in milliseconds; a scan to the end of the
        word from each of them is over a hundred million steps, minutes in Python. The bound is loose on purpose."""
        for shape, word in (("closed, no separator", "{a}" * 16000), ("never closed", "{" * 16000), ("nested, never closed", "{a" * 16000 + ",b")):
            with self.subTest(shape=shape):
                started = time.monotonic()
                self.assertEqual(self.guard.brace_expand(word), [word])
                self.assertLess(time.monotonic() - started, 5.0)

    def test_the_default_budget_covers_a_long_real_word(self) -> None:
        """40 KB, longer than any command in three censuses of about 41,000 recent real ones (38,482 characters at
        most), with all 64 alternatives and a nested list."""
        word = "{a,{b,c},d}" + "{e,f}" * 4 + "x" * 40000
        self.assertEqual(len(self.guard.brace_expand(word)), 4 * 2**4 + 1)

    def test_a_word_past_the_scan_budget_is_refused(self) -> None:
        """Fail closed, at the exact character: the budget's worth is scanned, one more is refused."""
        budget = self.guard.BRACE_SCAN_BUDGET
        self.assertEqual(len(self.guard.brace_expand("{a,b}" + "y" * (budget - 5))), 3)
        with self.assertRaisesRegex(self.guard.MalformedInput, "scans more than %d characters" % budget):
            self.guard.brace_expand("{a,b}" + "y" * (budget - 4))

    def test_a_word_with_no_brace_is_never_charged(self) -> None:
        word = "y" * (self.guard.BRACE_SCAN_BUDGET + 1)
        self.assertEqual(self.guard.brace_expand(word), [word])

    def test_each_list_part_is_charged_when_it_is_expanded(self) -> None:
        """Two words of one length. The flat one is inside the budget; the one whose first part holds a list is
        scanned twice over that part, and is past it."""
        self.guard.BRACE_SCAN_BUDGET = self.SMALL_BUDGET
        flat = "{" + "y" * 605 + ",z}"
        nested = "{" + "{b,c}" + "y" * 600 + ",z}"
        self.assertEqual((len(flat), len(nested)), (609, 609))
        self.assertEqual(len(self.guard.brace_expand(flat)), 3)
        with self.assertRaisesRegex(self.guard.MalformedInput, "BRACE_SCAN_BUDGET"):
            self.guard.brace_expand(nested)

    def test_the_budget_is_per_call(self) -> None:
        """One call's scan does not come out of the next call's budget."""
        self.guard.BRACE_SCAN_BUDGET = self.SMALL_BUDGET
        word = "{a,b}" + "y" * 600
        for _ in range(3):
            self.assertEqual(len(self.guard.brace_expand(word)), 3)

    def test_the_hook_fails_closed_past_the_scan_budget(self) -> None:
        """End to end: exit 2 and nothing on stdout, for a word that would assemble ``.ssh`` had it been expanded."""
        self.guard.BRACE_SCAN_BUDGET = self.SMALL_BUDGET
        word = ".ss{h,x}/" + "y" * self.SMALL_BUDGET
        self.assertNotIn(".ssh", word)
        self.assert_refused("Bash", {"command": "cat ~/" + word}, "scans more than %d characters" % self.SMALL_BUDGET)
        self.assert_refused("Glob", {"pattern": "~/" + word}, "BRACE_SCAN_BUDGET")
        code, out, err = self._hook("Bash", {"command": "cat ~/" + word[: self.SMALL_BUDGET // 2]})
        self.assertEqual(code, 0, err)
        self.assertIn("CRED-PATH-BASH", out)  # the same word, short enough to scan, is denied


if __name__ == "__main__":
    unittest.main()
