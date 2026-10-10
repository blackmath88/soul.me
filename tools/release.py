#!/usr/bin/env python3
"""Staged review (D-027): move the next staged batch from data/staged/ into inbox/, one at a time.

Usage: python tools/release.py <vault> [--max-pending 1] [--today YYYY-MM-DD] [--list]

Bulk imports (`extract.py --stage`, `classify_corrections.py --stage`) wait in data/staged/, which is never
committed. A batch is released only while fewer than --max-pending files wait in inbox/, so the weekly review
stays short. Corrections go first (the Operating manual changes the most for the least reading), then the oldest.
Releasing adds `released: <today>`: the 4-week expiry (D-012) counts from there. A batch that fails the
validator stays staged.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import validate  # noqa: E402


def queue(vault):
    return sorted((Path(vault) / "data" / "staged").glob("*.md"), key=lambda p: ("corrections" not in p.name, p.name))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--max-pending", type=int, default=1, help="release only while fewer inbox files wait (default 1)")
    ap.add_argument("--today")
    ap.add_argument("--list", action="store_true", help="show the queue, release nothing")
    a = ap.parse_args()
    vault = Path(a.vault)
    today = a.today or datetime.date.today().isoformat()
    staged = queue(vault)
    if a.list or not staged:
        print("\n".join(f"{i}. {p.name}" for i, p in enumerate(staged, 1)) or "nothing staged")
        return
    pending = sorted((vault / "inbox").glob("*.md"))
    if len(pending) >= a.max_pending:
        print(f"{len(pending)} inbox file(s) still waiting ({', '.join(p.name for p in pending)}); "
              f"seal or delete them first. {len(staged)} batch(es) staged.")
        return
    src = staged[0]
    dest = vault / "inbox" / src.name
    if dest.exists():
        sys.exit(f"{dest} already exists; rename the staged file")
    text = src.read_text(encoding="utf-8")
    text, n = re.subn(r"^(updated:.*)$", rf"released: {today}\n\1", re.sub(r"^released:.*\n", "", text, flags=re.M),
                      count=1, flags=re.M)
    if not n:
        sys.exit(f"{src.name}: no updated: line in the frontmatter")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    errors = [e for e in validate(vault)[1] if e.startswith(f"inbox/{dest.name}:")]
    if errors:
        dest.unlink()
        sys.exit("not released, the batch fails the validator:\n" + "\n".join(errors))
    src.unlink()
    print(f"released {dest.relative_to(vault)} (expires 4 weeks after {today}); {len(staged) - 1} batch(es) still staged")


if __name__ == "__main__":
    main()
