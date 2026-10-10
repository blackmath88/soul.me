#!/usr/bin/env python3
"""Checks tools/conflicts.py against the stub model on a copy of the fictional vault.  python tests/test_conflicts.py"""
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = "8766"


class Conflicts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stub = subprocess.Popen([sys.executable, str(ROOT / "tests" / "stub_llm.py"), PORT])
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.stub.terminate()
        cls.stub.wait()

    def test_pairs_are_real_lines(self):
        tmp = Path(tempfile.mkdtemp(prefix="soulme-conflicts-"))
        try:
            vault = tmp / "vault"
            shutil.copytree(ROOT / "vault", vault)
            t = vault / "topics" / "tools.md"
            t.write_text(t.read_text() + "- [stated] Writes in Obsidian and keeps one vault for work, one for private notes\n")
            p = subprocess.run([sys.executable, str(ROOT / "tools" / "conflicts.py"), str(vault), "--base",
                                f"http://127.0.0.1:{PORT}/v1", "--model", "stub", "--today", "2026-10-01"],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("**duplicate**", p.stdout)
            self.assertIn("one for private notes", p.stdout)
            self.assertNotIn("invented", p.stdout)                      # unknown id dropped
            self.assertNotIn("self", p.stdout)                          # self-pair dropped
            self.assertIn("2 dropped", p.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_tensions_and_archive_never_sent(self):
        sys.path.insert(0, str(ROOT / "tools"))
        from conflicts import live_lines
        tmp = Path(tempfile.mkdtemp(prefix="soulme-conflicts-"))
        try:
            vault = tmp / "vault"
            shutil.copytree(ROOT / "vault", vault)
            t = vault / "topics" / "tools.md"
            t.write_text(t.read_text() + "# Archive\n- [stated] An archived tool choice\n")
            import datetime
            texts = " ".join(text for _, _, text in live_lines(vault, datetime.date(2026, 10, 1)))
            self.assertIn("Obsidian", texts)
            self.assertNotIn("rigid agendas", texts)                     # ## Tensions: kept on purpose
            self.assertNotIn("archived tool choice", texts)
            self.assertNotIn("half marathon", texts)                     # inbox
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
