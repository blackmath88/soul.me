#!/usr/bin/env python3
"""Interview (v1): your own model asks a few questions where the vault is thin; your answers become a self note.

Usage: python tools/interview.py <vault> [-n 5] [--base URL] [--model NAME]

Runs locally like tools/extract.py (same --base/--model and SOULME_LLM_* variables). The model sees your live
[stated] lines, the open `questions:` from inbox files and the standard list in prompts/how-i-work.md, and picks
-n questions (prompts/interview.md). You answer in the terminal; an empty answer skips, a very short one gets one
"can you give an example?". Only your answers are written, one paragraph each, to vault/data/<date>-interview.md,
so the note holds your words only. Then: python tools/extract.py vault/data/<date>-interview.md --source self
Nothing is written to live files or the inbox.
"""
import argparse
import datetime
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chatgpt_export import refuse_repo_output  # noqa: E402
from extract import LLM, PROMPTS, fill, prompt_text, vault_lines  # noqa: E402
from validate import split_frontmatter  # noqa: E402

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["questions"],
          "properties": {"questions": {"type": "array", "items": {"type": "string"}}}}
SHORT = 8                                     # words; below this, ask for an example once


def open_gaps(vault):
    gaps = []
    for p in sorted((Path(vault) / "inbox").glob("*.md")):
        parts = split_frontmatter(p.read_text(encoding="utf-8"))
        fm = (yaml.safe_load(parts[0]) if parts else None) or {}
        gaps += [q for q in (fm.get("questions") or []) if isinstance(q, str) and q not in gaps]
    return gaps


def standard_questions():
    text = (PROMPTS / "how-i-work.md").read_text(encoding="utf-8")
    return re.findall(r"^\d+\. (.+)$", text.split("## Optional")[0], re.M)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("-n", type=int, default=5, help="questions to ask (default 5)")
    ap.add_argument("--base", default=os.environ.get("SOULME_LLM_BASE", "http://localhost:11434/v1"))
    ap.add_argument("--model", default=os.environ.get("SOULME_LLM_MODEL"))
    ap.add_argument("--key", default=os.environ.get("SOULME_LLM_KEY"))
    ap.add_argument("--today")
    a = ap.parse_args()
    if not a.model:
        sys.exit("set --model or SOULME_LLM_MODEL")
    today = (datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()).isoformat()
    out, k = Path(a.vault) / "data" / f"{today}-interview.md", 2
    refuse_repo_output(out)
    while out.exists():                       # never overwrite an earlier note
        out, k = out.with_name(f"{today}-interview-{k}.md"), k + 1

    vault = "\n".join(f"{f}: {t}" for f, t in vault_lines(a.vault)) or "(empty)"
    got = LLM(a.base, a.model, a.key).json(fill(prompt_text("interview.md"), n=str(a.n), vault=vault,
                                                gaps="\n".join(open_gaps(a.vault)) or "(none)",
                                                standard="\n".join(standard_questions())), SCHEMA, "interview")
    questions = [q.strip() for q in (got or {}).get("questions", []) if isinstance(q, str) and q.strip()][:a.n]
    if not questions:
        sys.exit("the model returned no questions")

    print("Answer in full sentences: only your answers are saved, not the questions. Empty line skips.\n", file=sys.stderr)
    answers = []
    for i, q in enumerate(questions, 1):
        print(f"{i}/{len(questions)} {q}", file=sys.stderr)
        ans = sys.stdin.readline().strip()
        if ans and len(ans.split()) < SHORT:
            print("   Can you give an example?", file=sys.stderr)
            more = sys.stdin.readline().strip()
            ans = f"{ans} {more}".strip()
        if ans:
            answers.append(ans)
    if not answers:
        print("nothing answered, nothing written", file=sys.stderr)
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(answers) + "\n", encoding="utf-8")
    print(f"\n{len(answers)} answers written to {out}\nnext: python tools/extract.py {out} --source self", file=sys.stderr)


if __name__ == "__main__":
    main()
