#!/usr/bin/env python3
"""Checks tools/curate.py on a copy of the fictional vault.  python tests/test_curate.py"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def digest(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.rglob("*")) if p.is_file()}


class Curate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="soulme-curate-"))
        self.vault = self.tmp / "vault"
        shutil.copytree(ROOT / "vault", self.vault)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_curate(self, today):
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "curate.py"), str(self.vault), "--today", today],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def test_report(self):
        t = self.vault / "topics" / "tools.md"
        t.write_text(t.read_text() + "- [stated] Writes in Obsidian and keeps one vault for work, one for private notes\n"
                     "# Archive\n- [stated] (valid_to: 2025-01) An old archived fact\n")
        before = digest(self.vault)
        out = self.run_curate("2027-01-20")
        self.assertEqual(before, digest(self.vault))                       # read-only
        self.assertIn("inbox/2026-09-28-chatgpt-dump.md", out)
        self.assertIn("sessions/2026-09-25-cohort-3-agenda.md", out)
        self.assertIn("Contract runs until the end of December 2026 (valid_to 2026-12)", out)
        self.assertNotIn("An old archived fact", out)                     # already archived
        self.assertIn("Possible duplicates", out)
        self.assertIn("keeps one vault for work", out)

    def test_released_counts_from_release(self):
        i = self.vault / "inbox" / "2026-09-28-chatgpt-dump.md"
        i.write_text(i.read_text().replace("updated:", "released: 2026-12-20\nupdated:", 1))
        out = self.run_curate("2027-01-10")
        self.assertNotIn("2026-09-28-chatgpt-dump.md", out.split("## Sessions")[0])   # 21 days since release

    def test_quiet_when_fresh(self):
        out = self.run_curate("2026-10-01")
        self.assertEqual(out.count("- none"), 5)

    def test_apply(self):
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "curate.py"), str(self.vault), "--today", "2027-01-20",
                              "--apply"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("applied in this PR", out.stdout)
        self.assertFalse((self.vault / "inbox" / "2026-09-28-chatgpt-dump.md").exists())
        self.assertFalse((self.vault / "sessions" / "2026-09-25-cohort-3-agenda.md").exists())
        area = (self.vault / "areas" / "nordhafen-pilot.md").read_text()
        live, archived = area.split("# Archive")
        self.assertNotIn("Contract runs until", live)
        self.assertIn("- [stated] (valid_to: 2026-12) Contract runs until the end of December 2026", archived)  # word for word
        self.assertIn("updated: 2027-01-20", area)
        v = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py"), str(self.vault)], capture_output=True, text=True)
        self.assertEqual(v.returncode, 0, v.stdout)
        again = self.run_curate("2027-01-20")                                   # nothing left to do
        self.assertEqual(again.count("- none"), 5)                              # nothing left to do
        e = subprocess.run([sys.executable, str(ROOT / "tools" / "export.py"), str(self.vault), "--profile", "personal",
                            "--target", "system", "--today", "2026-10-01"], capture_output=True, text=True)
        self.assertNotIn("Contract runs until", e.stdout)                       # archived lines never leave the vault

    def test_flags_ids_and_denylist(self):
        t = self.vault / "topics" / "tools.md"
        t.write_text(t.read_text() + "- [stated] Pays the coach from CH93 0076 2011 6238 5295 7\n"
                     "- [stated] Keeps the Nordhafen Q3 numbers in a separate folder\n")
        (self.vault / "data" / "denylist.txt").write_text("Nordhafen\n")
        before = digest(self.vault)
        out = self.run_curate("2026-10-01")
        self.assertEqual(before, digest(self.vault))
        section = out.split("## Possible IDs")[1]
        self.assertIn("(iban): Pays the coach from <iban>", section)
        self.assertNotIn("6238", out)                                           # masked, not repeated
        self.assertIn("(denylist): Keeps the <denylist> Q3 numbers", section)
        self.assertIn("`people/jonas-brandt.md` (denylist): Sponsor of the <denylist> pilot", section)


if __name__ == "__main__":
    unittest.main(verbosity=2)
