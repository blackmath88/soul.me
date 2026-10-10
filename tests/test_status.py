#!/usr/bin/env python3
"""Checks tools/status.py: the mark follows the vault's numbers.  python tests/test_status.py"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from status import GREY, OWN, SHU, svg  # noqa: E402


class Status(unittest.TestCase):
    def test_states(self):
        nothing = svg(0, 3)
        self.assertIn(GREY["s"], nothing)                      # grey until something is sealed
        self.assertNotIn(OWN["f"], nothing)
        self.assertIn("0 sealed · 3 to seal", nothing)
        owned = svg(12, 0)
        self.assertIn(OWN["f"], owned)
        self.assertNotIn(SHU, owned)                           # no seal without lines to seal
        self.assertIn('aria-label="soul.me: 12 sealed"', owned)
        self.assertIn(SHU, svg(12, 2))

    def test_fictional_vault(self):
        out = __import__("subprocess").run([sys.executable, str(ROOT / "tools" / "status.py"), str(ROOT / "vault")],
                                           capture_output=True, text=True).stdout
        self.assertTrue(out.startswith("<svg"))
        self.assertIn("44 sealed · 4 to seal", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
