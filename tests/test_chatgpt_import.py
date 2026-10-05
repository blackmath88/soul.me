#!/usr/bin/env python3
"""Runs tools/chatgpt_export.py and tools/chatgpt_corrections.py on the fictional export in
tests/fixtures/chatgpt-mara/ and checks the promises in docs/chatgpt-import.md.

  python tests/test_chatgpt_import.py

Every file the tools open is recorded with a Python audit hook, so reading user.json (or anything else
outside the allowlist, D-021) fails the test.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "chatgpt-mara"
ALLOWED = {"conversations-000.json", "conversations-001.json", "conversation_asset_file_names.json", "library_files.json"}

WRAP = r'''
import os, runpy, sys
opened = []
def hook(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        opened.append(os.fsdecode(args[0]))
sys.addaudithook(hook)
tool = sys.argv[1]
sys.argv = sys.argv[1:]
try:
    runpy.run_path(tool, run_name="__main__")
finally:
    sys.stderr.write("\nOPENED:" + "\x1f".join(opened) + "\n")
'''


def run(tool, *args):
    p = subprocess.run([sys.executable, "-c", WRAP, str(ROOT / "tools" / tool), *map(str, args)],
                       capture_output=True, text=True)
    opened = p.stderr.rsplit("OPENED:", 1)[-1].strip().split("\x1f")
    fixture_files = {Path(o).name for o in opened if Path(o).resolve().parent == FIX.resolve()}
    return p, fixture_files


class ChatGPTImport(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="soulme-chatgpt-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_export(self):
        out = self.tmp / "out"
        p, opened = run("chatgpt_export.py", FIX, out)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertLessEqual(opened, ALLOWED, f"opened outside the allowlist: {opened - ALLOWED}")
        files = sorted(f.name for f in out.glob("*.md"))
        self.assertEqual(files, ["2026-06-03_retro-format_a1b2c3d4.md", "2026-07-15_kickoff-agenda_e5f6a7b8.md",
                                 "2026-08-20_weekly-notes_c9d0e1f2.md", "2026-09-10_new-chat_aa11aa11.md",
                                 "2026-09-10_new-chat_bb22bb22.md"])          # same date + title, no collision
        text = {f: (out / f).read_text(encoding="utf-8") for f in files}
        everything = "\n".join(text.values())
        self.assertIn('[pasted: 3,111 chars, starts "Draft agenda for the cohort 3 kickoff', text[files[1]])
        self.assertNotIn("09:20 Round of expectations. 09:00", everything)      # the pasted body itself is gone
        self.assertIn("[attachment: notes-template.docx]", text[files[2]])       # via conversation_asset_file_names.json
        self.assertIn("[attachment: cohort-3-plan.pdf]", text[files[2]])        # via library_files.json
        self.assertIn("[attachment]\n", text[files[2]])                          # unknown pointer
        self.assertNotIn("ABANDONED BRANCH", everything)                         # active branch only
        self.assertNotIn("Hidden profile text", everything)                      # hidden context skipped
        self.assertNotIn("MUST-NOT-BE-READ", everything)
        stats = json.loads((out / "_stats.json").read_text())
        self.assertEqual(stats["conversations"], 7)
        self.assertEqual(stats["kept"], 5)
        self.assertEqual(stats["skipped"], {"fewer_than_2_user_turns": 1, "under_300_authored_chars": 1})
        self.assertGreater(stats["chars"]["pasted"], stats["chars"]["authored"])  # pasted doesn't count as authored
        self.assertEqual(stats["kept_per_year"], {"2026": 5})
        self.assertEqual(stats["date_range"], ["2026-06-03", "2026-09-10"])

    def test_assistant_truncated(self):
        out = self.tmp / "out"
        run("chatgpt_export.py", FIX, out)
        t = (out / "2026-06-03_retro-format_a1b2c3d4.md").read_text(encoding="utf-8")
        first = t.split("## assistant\n\n")[1].split("\n\n## ")[0]
        self.assertTrue(first.endswith("…"))
        self.assertLessEqual(len(first), 601)

    def test_corrections(self):
        out = self.tmp / "corr.jsonl"
        p, opened = run("chatgpt_corrections.py", FIX, out)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertLessEqual(opened, ALLOWED, f"opened outside the allowlist: {opened - ALLOWED}")
        rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(rows), 7)
        for r in rows:
            self.assertEqual(set(r), {"conv_id", "date", "title", "user", "prev_assistant", "hint"})
            self.assertLessEqual(len(r["user"]), 300)
            self.assertLessEqual(len(r["prev_assistant"]), 300)
        by_user = {r["user"]: r for r in rows}
        self.assertTrue(by_user["Kürzer bitte, und ohne Einleitung."]["hint"])
        self.assertTrue(by_user["Nicht drei Optionen, nur eine Empfehlung bitte."]["hint"])
        self.assertFalse(by_user["Thanks, perfect."]["hint"])                  # emitted anyway: hint is not a filter
        self.assertNotIn("ABANDONED BRANCH", out.read_text(encoding="utf-8"))

    def test_refuses_output_inside_repo(self):
        for tool, target in (("chatgpt_export.py", ROOT / "tests" / "_out"), ("chatgpt_corrections.py", ROOT / "corr.jsonl")):
            p, _ = run(tool, FIX, target)
            self.assertNotEqual(p.returncode, 0)
            self.assertIn("refusing to write inside the soul.me repo", p.stderr)
            self.assertFalse(target.exists())

    def test_worked_example_validates(self):
        vault = self.tmp / "vault"
        shutil.copytree(ROOT / "vault", vault)
        shutil.copy(ROOT / "prompts" / "examples" / "mara-corrections-inbox.md", vault / "inbox" / "2026-10-05-chatgpt-corrections.md")
        ok = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py"), vault], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        live = vault / "topics" / "tools.md"
        live.write_text(live.read_text() + "- [stated] (seen: 2) Not allowed in a live file\n")
        bad = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py"), vault], capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("(seen: n) is only allowed in inbox/", bad.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
