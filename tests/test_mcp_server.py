#!/usr/bin/env python3
"""Checks tools/mcp_server.py over stdio on a copy of the fictional vault.  python tests/test_mcp_server.py"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def digest(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and "inbox" not in p.parts}


class Server(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="soulme-mcp-"))
        self.vault = self.tmp / "vault"
        shutil.copytree(ROOT / "vault", self.vault)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def session(self, profile, calls, *flags, today="2026-10-01"):
        """Run initialize + calls; return {id: result} for the calls (ids from 2)."""
        msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                {"jsonrpc": "2.0", "method": "notifications/initialized"}]
        for i, (method, params) in enumerate(calls, 2):
            msgs.append({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
        p = subprocess.run([sys.executable, str(ROOT / "tools" / "mcp_server.py"), str(self.vault), "--profile", profile,
                            "--client", "claude-home", "--today", today, *flags],
                           input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        replies = [json.loads(l) for l in p.stdout.splitlines()]
        self.assertEqual(len(replies), len(calls) + 1)                     # the notification gets no reply
        return {r["id"]: r.get("result", r.get("error")) for r in replies}

    def call(self, profile, name, flags=(), today="2026-10-01", **args):
        r = self.session(profile, [("tools/call", {"name": name, "arguments": args})], *flags, today=today)[2]
        return r["content"][0]["text"], r["isError"]

    def test_tools_per_profile(self):
        names = lambda r: [t["name"] for t in r["tools"]]
        personal = self.session("personal", [("tools/list", {})])[2]
        work = self.session("work", [("tools/list", {})], "--read-only")[2]
        self.assertIn("last_handoff", names(personal))
        self.assertIn("propose", names(personal))
        self.assertNotIn("last_handoff", names(work))                       # D-022: no sessions at work
        self.assertNotIn("propose", names(work))                            # --read-only

    def test_only_confirmed_lines_leave(self):
        core, _ = self.call("personal", "get_core")
        self.assertIn("# Operating manual", core)
        self.assertNotIn("half marathon", core)                             # an inbox line
        found, _ = self.call("personal", "search", query="half marathon training")
        self.assertNotIn("inbox/", found)
        now, _ = self.call("personal", "read", path="areas/nordhafen-pilot.md")
        later, _ = self.call("personal", "read", path="areas/nordhafen-pilot.md", today="2027-02-01")
        self.assertIn("Contract runs until", now)
        self.assertNotIn("Contract runs until", later)                      # past valid_to

    def test_work_profile_hides_people(self):
        text, err = self.call("work", "read", path="people/jonas-brandt.md")
        self.assertTrue(err)
        listing, _ = self.call("work", "list")
        found, _ = self.call("work", "search", query="slide deck anecdotes")
        self.assertNotIn("people/", listing + found)
        self.assertIn("people/jonas-brandt.md", self.call("personal", "search", query="slide deck anecdotes")[0])

    def test_propose_writes_inbox_only(self):
        before = digest(self.vault)
        text, err = self.call("personal", "propose", path="topics/tools.md",
                              lines=["Uses [stated] Miro for cohort boards", "Uses Miro for cohort boards", ""])
        self.assertFalse(err, text)
        self.assertEqual(before, digest(self.vault))                        # live files untouched
        inbox = (self.vault / "inbox" / "2026-10-01-mcp-claude-home.md").read_text()
        self.assertIn("## → topics/tools.md\n- [inferred] Uses (stated) Miro for cohort boards\n", inbox)
        self.assertNotIn("[stated]", inbox)                                 # a tool never writes [stated]
        self.call("personal", "propose", path="minime.md", lines=["Prefers mornings for deep work"], told=True)
        inbox = (self.vault / "inbox" / "2026-10-01-mcp-claude-home.md").read_text()
        self.assertIn("- [imported:claude-home] Prefers mornings for deep work", inbox)
        v = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py"), str(self.vault)], capture_output=True, text=True)
        self.assertEqual(v.returncode, 0, v.stdout)
        for bad in ("people/jonas-brandt.md", "../../etc/passwd", "inbox/x.md", "sessions/x.md"):
            _, err = self.call("work", "propose", path=bad, lines=["x"])
            self.assertTrue(err, bad)

    def test_handoff_and_errors(self):
        text, _ = self.call("personal", "last_handoff")
        self.assertIn("cohort 3 kickoff agenda", text)
        r = self.session("personal", [("tools/call", {"name": "nope", "arguments": {}}), ("bogus/method", {})])
        self.assertEqual(r[2]["code"], -32602)
        self.assertEqual(r[3]["code"], -32601)


if __name__ == "__main__":
    unittest.main(verbosity=2)
