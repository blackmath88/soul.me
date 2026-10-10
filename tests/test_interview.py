#!/usr/bin/env python3
"""Checks tools/interview.py against the stub model.  python tests/test_interview.py"""
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = "8767"


class Interview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stub = subprocess.Popen([sys.executable, str(ROOT / "tests" / "stub_llm.py"), PORT])
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.stub.terminate()
        cls.stub.wait()

    def run_interview(self, vault, answers):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "interview.py"), str(vault), "-n", "3", "--base",
                               f"http://127.0.0.1:{PORT}/v1", "--model", "stub", "--today", "2026-10-10"],
                              input=answers, capture_output=True, text=True)

    def test_only_answers_are_saved(self):
        tmp = Path(tempfile.mkdtemp(prefix="soulme-interview-"))
        try:
            vault = tmp / "vault"
            shutil.copytree(ROOT / "vault", vault)
            i = vault / "inbox" / "2026-09-28-chatgpt-dump.md"
            i.write_text(i.read_text().replace("updated:", 'questions: ["Which meetings drain Mara most?"]\nupdated:', 1))
            answers = ("Short loops.\nTwo-week tests, then a review with the sponsor before anything grows.\n"
                       "\n"
                       "I want answers in English, short, with the recommendation first and the steps after it.\n")
            p = self.run_interview(vault, answers)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("1/3 Which meetings drain Mara most?", p.stderr)     # open gap asked first
            self.assertIn("Can you give an example?", p.stderr)                # short answer, one follow-up
            note = (vault / "data" / "2026-10-10-interview.md").read_text()
            self.assertEqual(note.count("\n\n"), 1)                            # two answers, one skipped
            self.assertIn("Short loops. Two-week tests", note)
            self.assertNotIn("?", note)                                        # no question text in the note
            p2 = self.run_interview(vault, "Another long enough answer about how I like to plan my week.\n\n\n")
            self.assertTrue((vault / "data" / "2026-10-10-interview-2.md").exists())   # never overwrites
            self.assertEqual(p2.returncode, 0, p2.stderr)
            live = sorted(x.relative_to(vault).as_posix() for x in vault.rglob("*.md") if "data" not in x.parts)
            self.assertNotIn("interview", " ".join(live))                     # nothing outside data/
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_refuses_inside_repo(self):
        p = self.run_interview(ROOT / "vault", "x\n")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("refusing to write inside", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
