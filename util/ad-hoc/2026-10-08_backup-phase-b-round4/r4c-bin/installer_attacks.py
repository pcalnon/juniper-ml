#!/usr/bin/env python3
"""Round 4 lane C: attacks on the a0ff619c installer's real path, reusing the suite's own stub harness.

Run with cwd = the scratch a0 extraction:  python3 -m unittest -v <this file>   (PYTHONPATH=<a0>)
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.getcwd())
from tests.test_duplicati_installer_real_path import BLESSED, InstallerRealPath, _sha256  # noqa: E402

InstallerRealPath.__test__ = False  # do not re-run the suite's own tests here


class Attacks(InstallerRealPath):
    __test__ = True

    def test_a_symlinked_unit_is_copied_aside_by_content_and_its_target_left_alone(self):
        outside = self.tmp / "elsewhere"
        outside.mkdir()
        target = outside / "duplicati.service"
        target.write_text("[Unit]\nDescription=someone's linked unit\n", encoding="utf-8")
        before = _sha256(target)
        dst = self.prefix / "etc/systemd/system/duplicati.service"
        dst.symlink_to(target)
        r = self.run_installer()
        print("\n[A] rc", r.returncode, "| stderr tail:", r.stderr.strip().splitlines()[-1:] if r.stderr.strip() else "-")
        asides = sorted(p.name for p in dst.parent.glob("duplicati.service.pre-install-*"))
        print("[A] asides", asides, "| aside is symlink:", [(dst.parent / a).is_symlink() for a in asides])
        print("[A] dst is symlink after:", dst.is_symlink(), "| target unchanged:", _sha256(target) == before)
        if asides:
            print("[A] aside holds the target bytes:", _sha256(dst.parent / asides[0]) == before)

    def test_b_symlinked_lib_dir(self):
        outside = self.tmp / "libdir-elsewhere"
        outside.mkdir()
        (self.prefix / "usr/local/lib").mkdir(parents=True)
        (self.prefix / "usr/local/lib/duplicati").symlink_to(outside)
        r = self.run_installer()
        print("\n[B] rc", r.returncode, "| files landed in the link target:", sorted(p.name for p in outside.iterdir()))

    def test_c_rerun_after_first_install_over_preexisting_files_keeps_the_asides_and_takes_no_new_ones(self):
        dflt = self.prefix / "etc/default/duplicati"
        dflt.write_text("DAEMON_OPTS=\"--someones-own\"\n", encoding="utf-8")
        r1 = self.run_installer()
        a1 = sorted(p.name for p in dflt.parent.glob("duplicati.pre-install-*"))
        r2 = self.run_installer()
        a2 = sorted(p.name for p in dflt.parent.glob("duplicati.pre-install-*"))
        print("\n[C] rc1", r1.returncode, "rc2", r2.returncode, "| asides after run1", a1, "after run2", a2)

    def test_d_rerun_after_a_failure_between_install_and_bless(self):
        """Data-folder check fails AFTER the files are installed and BEFORE the bless: what does a re-run see?"""
        dflt = self.prefix / "etc/default/duplicati"
        dflt.write_text("DAEMON_OPTS=\"--someones-own\"\n", encoding="utf-8")
        r1 = self.run_installer(STUB_DATA_STAT="root:755")
        a1 = sorted(p.name for p in dflt.parent.glob("duplicati.pre-install-*"))
        print("\n[D] run1 rc", r1.returncode, "| blessed written:", self.blessed.exists(), "| asides", a1,
              "| installed == repo:", _sha256(dflt) == _sha256(self.repo / "util/systemd/duplicati.default"))
        r2 = self.run_installer()
        print("[D] run2 rc", r2.returncode, "| first-install message:", "first install" in r2.stdout,
              "| blessed now:", self.blessed.exists(), "| asides", sorted(p.name for p in dflt.parent.glob("duplicati.pre-install-*")))

    def test_e_nul_hidden_secret_in_contract(self):
        c = self.repo / "util/systemd/duplicati-env.contract"
        c.write_bytes(c.read_bytes() + b"SETTINGS_ENCRYPTION_\x00KEY=abcdefghijklmnopqrstu\n")
        r = self.run_installer("--dry-run")
        print("\n[E] dry-run rc", r.returncode, "| REFUSING lines:", [ln[:90] for ln in r.stderr.splitlines() if "REFUSING" in ln])

    def test_f_existing_env_is_a_symlink_to_a_refused_file(self):
        outside = self.tmp / "envtarget"
        outside.write_text("--disable-db-encryption\n", encoding="utf-8")
        (self.prefix / "etc/duplicati").mkdir(parents=True)
        (self.prefix / "etc/duplicati/env").symlink_to(outside)
        r = self.run_installer()
        print("\n[F] rc", r.returncode, "| refused:", any("REFUSING" in ln for ln in r.stderr.splitlines()))

    def test_g_blessed_lists_a_destination_twice(self):
        self.install_and_bless_current()
        lines = self.blessed.read_text(encoding="utf-8").splitlines()
        self.blessed.write_text("\n".join(lines + [lines[0]]) + "\n", encoding="utf-8")
        r = self.run_installer()
        print("\n[G] rc", r.returncode, "| first stderr lines:", r.stderr.strip().splitlines()[:2])

    def test_h_blessed_file_empty(self):
        self.install_and_bless_current()
        self.blessed.write_text("", encoding="utf-8")
        wrapper = self.prefix / BLESSED[0][1]
        wrapper.write_text(wrapper.read_text(encoding="utf-8") + "# someone's edit\n", encoding="utf-8")
        r = self.run_installer()
        asides = sorted(p.name for p in wrapper.parent.glob("duplicati-wrapper.bash.*"))
        print("\n[H] empty blessed + edited installed wrapper: rc", r.returncode, "| asides", asides,
              "| DRIFT reported:", "DRIFT" in r.stderr)

    def test_i_real_run_reports_the_asides_it_takes(self):
        dflt = self.prefix / "etc/default/duplicati"
        dflt.write_text("DAEMON_OPTS=\"--someones-own\"\n", encoding="utf-8")
        r = self.run_installer()
        out = r.stdout + r.stderr
        print("\n[I] pre-install real run rc", r.returncode, "| output names the aside:", "pre-install" in out,
              "| asides on disk:", sorted(p.name for p in dflt.parent.glob("duplicati.pre-install-*")))
        # (a no-op expression that called install_and_bless_current() under `if False` was removed for CodeQL)
        # drift: bless, edit installed, re-run with the switch
        r0 = self.run_installer()
        dflt.write_text(dflt.read_text(encoding="utf-8") + "# edit\n", encoding="utf-8")
        r2 = self.run_installer("--update-backup-behavior")
        out2 = r2.stdout + r2.stderr
        print("[I] drift real run rc", r0.returncode, r2.returncode, "| output names the .drifted copy:", ".drifted-" in out2,
              "| DRIFT line:", "DRIFT:" in out2, "| asides:", sorted(p.name for p in dflt.parent.glob("duplicati.drifted-*")))


if __name__ == "__main__":
    unittest.main()
