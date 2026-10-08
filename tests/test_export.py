#!/usr/bin/env python3
"""Checks tools/export.py on a copy of the fictional vault.

  python tests/test_export.py
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "export.py"


def export(vault, *args):
    p = subprocess.run([sys.executable, str(TOOL), str(vault), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="soulme-export-"))
        self.vault = self.tmp / "vault"
        shutil.copytree(ROOT / "vault", self.vault)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, rel, text):
        (self.vault / rel).write_text((self.vault / rel).read_text(encoding="utf-8") + text, encoding="utf-8")

    def test_never_inbox_or_sessions(self):
        _, out, _ = export(self.vault, "--profile", "personal", "--target", "system", "--today", "2026-10-08")
        self.assertNotIn("half marathon", out)              # only in inbox/
        self.assertNotIn("Drafted the cohort 3", out)       # only in sessions/
        self.assertNotIn("[stated]", out)
        self.assertNotIn("valid_from", out)
        self.assertIn("Lead with the answer, then the reasoning", out)

    def test_profiles(self):
        _, work, err = export(self.vault, "--profile", "work", "--target", "system", "--today", "2026-10-08")
        _, personal, _ = export(self.vault, "--profile", "personal", "--target", "system", "--today", "2026-10-08")
        self.assertIn("run-a-retro", work)                  # skills travel
        self.assertNotIn("jonas-brandt", work)              # people/ never at work
        self.assertNotIn("nordhafen-pilot", work)           # areas/ personal by default
        self.assertIn("jonas-brandt", personal)
        self.assertIn("3 files not in this profile", err)

    def test_profile_field(self):
        for rel in ("people/jonas-brandt.md", "topics/tools.md"):
            p = self.vault / rel
            p.write_text(p.read_text().replace("scope:", "profiles: [work, personal]\nscope:", 1))
        _, work, _ = export(self.vault, "--profile", "work", "--target", "system", "--today", "2026-10-08")
        self.assertIn("tools:", work)                       # a topic can opt into work
        self.assertNotIn("jonas-brandt", work)              # people/ cannot

    def test_validity(self):
        self.add("minime.md", "- [stated] (valid_to: 2026-09) An expired identity line\n- [stated] (valid_from: 2027-01) A future line\n")
        _, out, err = export(self.vault, "--profile", "personal", "--target", "system", "--today", "2026-10-08")
        self.assertNotIn("An expired identity line", out)
        self.assertNotIn("A future line", out)
        self.assertIn("Contract runs until the end of December 2026 (until 2026-12)", out)
        self.assertIn("skipped 2 outside their validity window", err)
        _, later, _ = export(self.vault, "--profile", "personal", "--target", "system", "--today", "2027-01-15")
        self.assertNotIn("Contract runs until the end of December", later)
        self.assertIn("A future line", later)

    def test_budget_order(self):
        code, out, err = export(self.vault, "--profile", "personal", "--target", "chatgpt", "--budget", "700", "--today", "2026-10-08")
        self.assertEqual(code, 0)
        about, how = out.split("=== How would you like ChatGPT to respond? ===\n")
        about = about.split("===\n", 1)[1]
        self.assertLessEqual(len(about), 700)
        self.assertLessEqual(len(how), 700)
        dropped = [l for l in err.splitlines() if l.startswith("  dropped")]
        self.assertTrue(dropped)
        # lowest priority goes first: once a manual line is dropped, no procedure line may remain
        if any("How to work with me" in l for l in dropped):
            self.assertNotIn("run-a-retro", how)
        self.assertIn("Lead with the answer", how)          # the top of the manual survives

    def test_deterministic_and_claude_files(self):
        a = export(self.vault, "--profile", "work", "--target", "system", "--today", "2026-10-08")[1]
        b = export(self.vault, "--profile", "work", "--target", "system", "--today", "2026-10-08")[1]
        self.assertEqual(a, b)
        out = self.tmp / "claude"
        code, _, _ = export(self.vault, "--profile", "personal", "--target", "claude", "--out", out, "--today", "2026-10-08")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ["context.md", "core.md", "procedures.md"])
        code, _, err = export(self.vault, "--profile", "work", "--target", "claude", "--out", ROOT / "tmp-export")
        self.assertNotEqual(code, 0)
        self.assertIn("refusing to write inside the soul.me repo", err)
        self.assertFalse((ROOT / "tmp-export").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
