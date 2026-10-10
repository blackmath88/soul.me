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
        self.assertEqual(out.count("- none"), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
