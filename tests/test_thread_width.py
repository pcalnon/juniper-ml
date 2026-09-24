#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for ``util/thread_width.py``, the perf lane's shared thread-width helper -- and the part of
it that makes the helper binding rather than advisory.

The lane lost two measurements to one hazard it had already written down. ``torch.get_num_threads()``
re-pins the calling thread's OpenMP width on a thread torch has not initialised, so an instrument
that reads it ends the burst it is measuring. The 2026-09-11 note recorded that; the 2026-09-16
width sweep walked into it anyway and concluded "Prose warnings do not bind. The guard belongs
*inside* a shared helper that instruments cannot bypass." The 2026-09-22 and 2026-09-23 handoffs
re-stated it as prose twice more. This file is where it stops being prose.

What it pins
------------
1. **The maps parser finds exactly the OpenMP runtimes.** GNU, Intel and LLVM, including a
   manylinux-renamed ``libgomp-<hash>.so.1`` -- the case where ``CDLL("libgomp.so.1")`` loads a
   second, independent runtime. It rejects ``libompd`` and offload plugins, a directory that merely
   contains ``libgomp``, and anonymous mappings; it de-duplicates segments and keeps a
   ``(deleted)`` runtime.
2. **The runtime handle can never load a library.** With none mapped, with two mapped, or with an
   unmapped path it raises BEFORE touching ``ctypes``; on the happy path it opens the mapped file
   with ``RTLD_NOLOAD``.
3. **The getter guard raises off the main thread and does not call through.** A raising guard that
   still ran the original would have already re-pinned the thread. It passes calls on the main
   thread and calls made from inside the ``torch`` package (the system's own behaviour), installs
   once, and its uninstaller never clobbers a later replacement.
4. **No instrument can bypass it.** An AST scan of ``util/ad-hoc/`` and ``util/experiments/``:
   opening an OpenMP runtime by a literal soname is refused, and so is referencing
   ``get_num_threads`` in a file that does not install the guard. The files that predate the
   helper are grandfathered BY NAME -- their evidence was produced by the code as it stands -- and
   every grandfathered file must still offend, so the list can only shrink. The scanner has its
   own negative controls: prose in a docstring or comment is not a call.

The helper imports without torch, and so does this file: CI has no torch. The real-runtime
claims are measured by ``util/thread_width.py --self-check`` in an environment that has it.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
HELPER = REPO_ROOT / "util" / "thread_width.py"
SCANNED_DIRS = (REPO_ROOT / "util" / "ad-hoc", REPO_ROOT / "util" / "experiments")

#: Instruments written before the helper existed. Each still offends; the evidence each produced
#: was produced by exactly this code, so rewriting them would falsify their provenance. Remove a
#: file from this set when it is converted -- the staleness check below makes that mandatory.
GRANDFATHERED = {
    "util/ad-hoc/2026-09-10_first_pass_library_attribution.py",
    "util/ad-hoc/2026-09-11_omp_icv_checkpoint_probe.py",
    "util/ad-hoc/2026-09-16_thread_width_arm.py",
    "util/ad-hoc/2026-09-17_epochs_completed_spread.py",
    "util/ad-hoc/2026-09-22_d6_epochs_completed_spread.py",
    "util/ad-hoc/2026-09-23_d1_epoch_count_sweep.py",
}

_DLOPENERS = {"CDLL", "PyDLL", "LoadLibrary"}


def _load_helper() -> types.ModuleType:
    name = "juniper_thread_width_under_test"
    spec = importlib.util.spec_from_file_location(name, HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # register BEFORE exec_module (dataclass / typing resolution)
    spec.loader.exec_module(module)
    return module


tw = _load_helper()


def _maps_line(path: str, perms: str = "r-xp") -> str:
    return f"7f0000000000-7f0000001000 {perms} 00000000 103:02 1234567                   {path}"


# ------------------------------------------------------------------------------------------------
# 1. the maps parser
# ------------------------------------------------------------------------------------------------
class ParseOpenMPRuntimesTest(unittest.TestCase):
    def test_finds_every_runtime_family_including_a_manylinux_rename(self) -> None:
        paths = [
            "/opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages/torch/lib/libgomp.so.1",
            "/opt/miniforge3/envs/X/lib/libgomp.so.1.0.0",
            "/venv/lib/python3.12/site-packages/torch.libs/libgomp-a34b3233.so.1",
            "/opt/intel/lib/libiomp5.so",
            "/usr/lib/llvm-18/lib/libomp.so.5",
        ]
        text = "\n".join(_maps_line(p) for p in paths)
        self.assertEqual(tw.parse_openmp_runtimes(text), paths)

    def test_rejects_near_misses(self) -> None:
        near_misses = [
            "/usr/lib/llvm-18/lib/libompd.so",  # OMPD debugging library, not a runtime
            "/usr/lib/x86_64-linux-gnu/libgomp-plugin-nvptx.so.1",  # offload plugin
            "/opt/libgomp-build/lib/libfoo.so",  # 'libgomp' in a DIRECTORY name
            "/usr/lib/libgompish.so.1",
            "/usr/lib/x86_64-linux-gnu/libopenblas.so.0",
        ]
        text = "\n".join(_maps_line(p) for p in near_misses)
        self.assertEqual(tw.parse_openmp_runtimes(text), [])

    def test_deduplicates_segments_and_keeps_first_mapped_order(self) -> None:
        gomp = "/env/lib/libgomp.so.1"
        iomp = "/env/lib/libiomp5.so"
        text = "\n".join([_maps_line(iomp, "r--p"), _maps_line(gomp, "r--p"), _maps_line(gomp, "r-xp"), _maps_line(iomp, "rw-p")])
        self.assertEqual(tw.parse_openmp_runtimes(text), [iomp, gomp])

    def test_a_deleted_runtime_is_still_the_runtime_in_use(self) -> None:
        text = _maps_line("/env/lib/libgomp.so.1 (deleted)")
        self.assertEqual(tw.parse_openmp_runtimes(text), ["/env/lib/libgomp.so.1"])

    def test_skips_anonymous_and_pseudo_mappings(self) -> None:
        text = "\n".join(
            [
                "7f0000000000-7f0000001000 rw-p 00000000 00:00 0",
                "7ffd00000000-7ffd00021000 rw-p 00000000 00:00 0                          [stack]",
                "55d000000000-55d000021000 rw-p 00000000 00:00 0                          [heap]",
            ]
        )
        self.assertEqual(tw.parse_openmp_runtimes(text), [])

    def test_this_process_can_be_read(self) -> None:
        if not os.path.exists(tw.MAPS_PATH):
            self.skipTest("no /proc/self/maps on this platform")
        self.assertIsInstance(tw.mapped_openmp_runtimes(), list)


# ------------------------------------------------------------------------------------------------
# 2. the runtime handle never loads a library
# ------------------------------------------------------------------------------------------------
class OpenMPRuntimeTest(unittest.TestCase):
    def _forbid_dlopen(self):
        return mock.patch.object(tw.ctypes, "CDLL", side_effect=AssertionError("dlopen must not be reached"))

    def test_nothing_mapped_raises_before_dlopen(self) -> None:
        with mock.patch.object(tw, "mapped_openmp_runtimes", return_value=[]), self._forbid_dlopen():
            with self.assertRaises(tw.OpenMPRuntimeNotMapped) as ctx:
                tw.OpenMPRuntime()
        self.assertIn("import", str(ctx.exception))

    def test_two_runtimes_raise_rather_than_guess(self) -> None:
        mapped = ["/env/lib/libgomp.so.1", "/env/lib/libiomp5.so"]
        with mock.patch.object(tw, "mapped_openmp_runtimes", return_value=mapped), self._forbid_dlopen():
            with self.assertRaises(tw.AmbiguousOpenMPRuntime):
                tw.OpenMPRuntime()

    def test_an_unmapped_path_is_refused_even_when_named(self) -> None:
        with mock.patch.object(tw, "mapped_openmp_runtimes", return_value=["/env/lib/libgomp.so.1"]), self._forbid_dlopen():
            with self.assertRaises(tw.OpenMPRuntimeNotMapped):
                tw.OpenMPRuntime("/usr/lib/x86_64-linux-gnu/libgomp.so.1")

    def test_opens_the_mapped_path_with_rtld_noload(self) -> None:
        fake_lib = mock.MagicMock()
        fake_lib.omp_get_max_threads.return_value = 7
        fake_lib.omp_get_num_procs.return_value = 16
        with mock.patch.object(tw, "mapped_openmp_runtimes", return_value=["/env/lib/libgomp.so.1"]), mock.patch.object(tw.ctypes, "CDLL", return_value=fake_lib) as cdll:
            omp = tw.OpenMPRuntime()
        cdll.assert_called_once()
        args, kwargs = cdll.call_args
        self.assertEqual(args[0], "/env/lib/libgomp.so.1")
        self.assertTrue(kwargs["mode"] & os.RTLD_NOLOAD, "the handle must be opened RTLD_NOLOAD so it can never load a second runtime")
        self.assertEqual(omp.path, "/env/lib/libgomp.so.1")
        self.assertEqual(omp.max_threads(), 7)
        self.assertEqual(omp.describe(), {"openmp_runtime": "/env/lib/libgomp.so.1", "omp_num_procs": 16})


# ------------------------------------------------------------------------------------------------
# 3. the getter guard
# ------------------------------------------------------------------------------------------------
def _fake_torch() -> types.SimpleNamespace:
    calls: list[str] = []

    def get_num_threads() -> int:
        calls.append(threading.current_thread().name)
        return 8

    return types.SimpleNamespace(get_num_threads=get_num_threads, calls=calls)


def _on_thread(fn):
    box: dict[str, object] = {}

    def run() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:  # handed back to the test, which asserts on it
            box["error"] = exc

    worker = threading.Thread(target=run, name="measured-thread")
    worker.start()
    worker.join()
    return box


def _call_the_getter():
    # ``globals()`` is the function's own globals, which _caller_in_module replaces.
    return globals()["torch"].get_num_threads()


def _caller_in_module(module_name: str, fake_torch: types.SimpleNamespace):
    """``_call_the_getter`` re-homed so its frame's ``__name__`` is ``module_name``.

    The guard identifies its caller by the calling frame's module name. Rebinding a function's
    globals gives that frame any module name without executing generated source.
    """
    return types.FunctionType(_call_the_getter.__code__, {"__name__": module_name, "torch": fake_torch}, "caller")


class TorchGetterGuardTest(unittest.TestCase):
    def test_raises_off_the_main_thread_without_calling_through(self) -> None:
        torch = _fake_torch()
        tw.install_torch_getter_guard(torch)
        box = _on_thread(torch.get_num_threads)
        self.assertIsInstance(box.get("error"), tw.ThreadWidthHazard)
        # A guard that raised AFTER calling the original would already have re-pinned the thread.
        self.assertEqual(torch.calls, [], "the original getter must not run on the measured thread")

    def test_passes_on_the_main_thread(self) -> None:
        torch = _fake_torch()
        tw.install_torch_getter_guard(torch)
        self.assertIs(threading.current_thread(), threading.main_thread())
        self.assertEqual(torch.get_num_threads(), 8)
        self.assertEqual(torch.calls, ["MainThread"])

    def test_passes_calls_made_from_inside_the_torch_package(self) -> None:
        torch = _fake_torch()
        tw.install_torch_getter_guard(torch)
        box = _on_thread(_caller_in_module("torch.utils.fake_internal", torch))
        self.assertEqual(box.get("value"), 8, box.get("error"))

    def test_a_module_merely_named_like_torch_is_not_exempt(self) -> None:
        torch = _fake_torch()
        tw.install_torch_getter_guard(torch)
        box = _on_thread(_caller_in_module("torchvision_lookalike", torch))
        self.assertIsInstance(box.get("error"), tw.ThreadWidthHazard)

    def test_install_is_idempotent(self) -> None:
        torch = _fake_torch()
        tw.install_torch_getter_guard(torch)
        first = torch.get_num_threads
        tw.install_torch_getter_guard(torch)
        self.assertIs(torch.get_num_threads, first, "a second install must not wrap the guard in another guard")
        self.assertTrue(getattr(torch.get_num_threads, tw.GUARD_MARKER))

    def test_uninstall_restores_and_never_clobbers_a_later_replacement(self) -> None:
        torch = _fake_torch()
        original = torch.get_num_threads
        uninstall = tw.install_torch_getter_guard(torch)
        uninstall()
        self.assertIs(torch.get_num_threads, original)

        uninstall = tw.install_torch_getter_guard(torch)

        def later() -> int:  # someone else's replacement, installed after the guard
            return 3

        torch.get_num_threads = later
        uninstall()
        self.assertIs(torch.get_num_threads, later)


# ------------------------------------------------------------------------------------------------
# 4. no instrument can bypass it
# ------------------------------------------------------------------------------------------------
def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def violations(source: str) -> list[str]:
    """What a scanned instrument must not do. Pure: text in, findings out."""
    tree = ast.parse(source)
    found: list[str] = []
    installs_guard = any(isinstance(node, ast.Call) and _call_name(node) == "install_torch_getter_guard" for node in ast.walk(tree))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in _DLOPENERS and node.args:
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str) and tw.OPENMP_RUNTIME_RE.search("/" + first.value.rsplit("/", 1)[-1]):
                found.append(f"line {node.lineno}: opens OpenMP runtime {first.value!r} by name; use thread_width.OpenMPRuntime()")
        getter_line = None
        if isinstance(node, ast.Attribute) and node.attr == "get_num_threads":
            getter_line = node.lineno
        elif isinstance(node, ast.Name) and node.id == "get_num_threads":
            getter_line = node.lineno
        if getter_line is not None and not installs_guard:
            found.append(f"line {getter_line}: references get_num_threads without install_torch_getter_guard()")
    return found


def stale_entries(entries: set[str], read) -> list[str]:
    """Grandfathered paths whose source no longer offends -- each must leave the list."""
    return sorted(rel for rel in entries if not violations(read(rel)))


def _scanned_files() -> list[Path]:
    files: list[Path] = []
    for directory in SCANNED_DIRS:
        files.extend(sorted(directory.rglob("*.py")))
    return files


class ScannerNegativeControlsTest(unittest.TestCase):
    """The scanner must catch the real shapes and must not fire on prose."""

    def test_catches_a_soname_open(self) -> None:
        self.assertTrue(violations('import ctypes\nlib = ctypes.CDLL("libgomp.so.1")\n'))
        self.assertTrue(violations('import ctypes\nlib = ctypes.cdll.LoadLibrary("libiomp5.so")\n'))

    def test_catches_a_getter_call_and_an_aliased_reference(self) -> None:
        self.assertTrue(violations("import torch\nn = torch.get_num_threads()\n"))
        # The bypass a call-only check misses: take the attribute, call it later.
        self.assertTrue(violations("import torch\nraw = torch.get_num_threads\nn = raw()\n"))
        self.assertTrue(violations("from torch import get_num_threads\nn = get_num_threads()\n"))

    def test_a_guarded_file_may_reference_the_getter(self) -> None:
        source = "import torch\nfrom thread_width import install_torch_getter_guard\ninstall_torch_getter_guard(torch)\nn = torch.get_num_threads()\n"
        self.assertEqual(violations(source), [])

    def test_prose_is_not_a_call(self) -> None:
        source = '"""Never read torch.get_num_threads(); never CDLL("libgomp.so.1")."""\n# torch.get_num_threads() re-pins\nx = "ctypes.CDLL(\'libgomp.so.1\')"\n'
        self.assertEqual(violations(source), [])

    def test_opening_a_mapped_path_is_allowed(self) -> None:
        self.assertEqual(violations("import ctypes\nlib = ctypes.CDLL(path, mode=0)\n"), [])
        self.assertEqual(violations('import ctypes\nlib = ctypes.CDLL("libopenblas.so.0")\n'), [])


class InstrumentsCannotBypassTest(unittest.TestCase):
    def test_the_scan_sees_the_instruments(self) -> None:
        # A scan over an empty or mis-rooted directory passes vacuously.
        files = _scanned_files()
        self.assertGreater(len(files), 50, f"scanned only {len(files)} files -- is SCANNED_DIRS right?")
        self.assertIn(REPO_ROOT / "util" / "ad-hoc" / "2026-09-23_d1_epoch_count_sweep.py", files)

    def test_no_instrument_outside_the_grandfathered_set_offends(self) -> None:
        offenders: dict[str, list[str]] = {}
        for path in _scanned_files():
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in GRANDFATHERED:
                continue
            try:
                found = violations(path.read_text(encoding="utf-8"))
            except SyntaxError as exc:
                self.fail(f"{rel} does not parse: {exc}")
            if found:
                offenders[rel] = found
        self.assertEqual(offenders, {}, "read the OpenMP width through util/thread_width.py (OpenMPRuntime + install_torch_getter_guard)")

    def test_every_grandfathered_file_still_offends(self) -> None:
        # A converted file left on the list would let a later edit re-introduce the hazard silently.
        stale = stale_entries(GRANDFATHERED, lambda rel: (REPO_ROOT / rel).read_text(encoding="utf-8"))
        self.assertEqual(stale, [], "these no longer offend; remove them from GRANDFATHERED")

    def test_the_staleness_check_can_fire(self) -> None:
        # Its real input is clean today, so without this the check could be deleted and stay green.
        sources = {"converted.py": "x = 1\n", "still_raw.py": 'import ctypes\nlib = ctypes.CDLL("libgomp.so.1")\n'}
        self.assertEqual(stale_entries(set(sources), sources.__getitem__), ["converted.py"])


class HelperImportsWithoutTorchTest(unittest.TestCase):
    def test_module_level_import_does_not_need_torch(self) -> None:
        # CI has no torch, and an instrument must be able to import the helper before torch.
        tree = ast.parse(HELPER.read_text(encoding="utf-8"))
        top_level = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        names = {alias.name.split(".")[0] for node in top_level for alias in node.names} | {node.module.split(".")[0] for node in top_level if isinstance(node, ast.ImportFrom) and node.module}
        self.assertNotIn("torch", names)


if __name__ == "__main__":
    unittest.main()
