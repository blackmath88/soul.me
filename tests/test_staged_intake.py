#!/usr/bin/env python3
"""Staged bulk intake on the fictional ChatGPT export, against the stub model:
chatgpt_export -> extract.py on a cluster folder --stage, chatgpt_corrections -> classify_corrections.py --stage,
then tools/release.py hands out one batch at a time (D-027).  python tests/test_staged_intake.py"""
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "chatgpt-mara"
PORT = "8769"
LLM = ["--base", f"http://127.0.0.1:{PORT}/v1", "--model", "stub"]


def tool(name, *args):
    p = subprocess.run([sys.executable, str(ROOT / "tools" / name), *map(str, args)], capture_output=True, text=True)
    assert p.returncode == 0, f"{name}: {p.stdout}\n{p.stderr}"
    return p.stdout + p.stderr


class StagedIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stub = subprocess.Popen([sys.executable, str(ROOT / "tests" / "stub_llm.py"), PORT])
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        cls.stub.terminate()
        cls.stub.wait()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="soulme-staged-"))
        self.vault = self.tmp / "vault"
        shutil.copytree(ROOT / "vault", self.vault)
        (self.vault / "inbox" / "2026-09-28-chatgpt-dump.md").unlink()     # start with an empty inbox
        conv = self.vault / "data" / "chatgpt" / "conversations"
        tool("chatgpt_export.py", FIX, conv)
        tool("chatgpt_corrections.py", FIX, self.vault / "data" / "chatgpt" / "corrections.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cluster_folder_reads_user_turns_only(self):
        sys.path.insert(0, str(ROOT / "tools"))
        from extract import load_messages
        msgs = load_messages(self.vault / "data" / "chatgpt" / "conversations")
        text = " ".join(m["text"] for m in msgs)
        self.assertIn("Kürzer bitte", text)
        self.assertNotIn("Here is a first draft", text)                     # assistant turns never read
        self.assertNotIn("[attachment", text)
        self.assertNotIn("[pasted:", text)
        self.assertEqual(len({m["conv"] for m in msgs}), 5)

    def test_corrections_seen_counts_across_batches(self):
        out = tool("classify_corrections.py", self.vault / "data" / "chatgpt" / "corrections.jsonl", "--vault", self.vault,
                   "--batch", "3", "--today", "2026-10-10", *LLM)
        self.assertIn("4 unknown ids dropped", out)                          # the stub adds c999 to every candidate
        inbox = (self.vault / "inbox" / "2026-10-10-chatgpt-home-corrections.md").read_text()
        self.assertIn("- [imported:chatgpt-home] (seen: 3) Keep answers short.", inbox)
        self.assertIn("- [imported:chatgpt-home] (seen: 2) Lead with one recommendation, not options.", inbox)
        self.assertEqual(inbox.count("Keep answers short."), 1)              # merged across batches
        self.assertIn("labels: {preference: 5, one-off: 1, noise: 1}", inbox)
        v = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py"), str(self.vault)], capture_output=True, text=True)
        self.assertEqual(v.returncode, 0, v.stdout)

    def test_stage_then_release_one_at_a_time(self):
        tool("extract.py", self.vault / "data" / "chatgpt" / "conversations", "--source", "chatgpt-home", "--vault",
             self.vault, "--stage", *LLM)
        tool("classify_corrections.py", self.vault / "data" / "chatgpt" / "corrections.jsonl", "--vault", self.vault,
             "--stage", "--today", "2026-10-10", *LLM)
        self.assertEqual(list((self.vault / "inbox").glob("*.md")), [])     # nothing reaches the inbox unreleased
        staged = tool("release.py", self.vault, "--list")
        self.assertIn("1. 2026-10-10-chatgpt-home-corrections.md", staged)  # corrections first
        out = tool("release.py", self.vault, "--today", "2026-10-12")
        self.assertIn("released inbox/2026-10-10-chatgpt-home-corrections.md", out)
        text = (self.vault / "inbox" / "2026-10-10-chatgpt-home-corrections.md").read_text()
        self.assertIn("released: 2026-10-12\nupdated: 2026-10-10", text)
        held = tool("release.py", self.vault, "--today", "2026-10-12")
        self.assertIn("still waiting", held)                                # one batch at a time
        self.assertEqual(len(list((self.vault / "inbox").glob("*.md"))), 1)
        (self.vault / "inbox" / "2026-10-10-chatgpt-home-corrections.md").unlink()     # the person sealed it
        out = tool("release.py", self.vault, "--today", "2026-10-19")
        self.assertIn("0 batch(es) still staged", out)
        report = tool("curate.py", self.vault, "--today", "2026-11-10")
        self.assertNotIn("days since released", report)                     # 22 days since release: not expired


if __name__ == "__main__":
    unittest.main(verbosity=2)
