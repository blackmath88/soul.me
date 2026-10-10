#!/usr/bin/env python3
"""Contradictions and duplicates across the vault (v3), judged by your own model. Read-only.

Usage: python tools/conflicts.py <vault> [--base URL] [--model NAME] [--today YYYY-MM-DD] >> report.md

Runs locally like tools/extract.py (same --base/--model and SOULME_LLM_* variables), never in the cloud Action:
it sends every live [stated] line to the model. `## Tensions` and `# Archive` are left out on purpose.
The model answers with line ids from prompts/curate-conflicts.md; unknown ids and self-pairs are dropped,
so every reported line exists word for word. Prints a markdown section to paste under the weekly curation PR.
"""
import argparse
import datetime
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export import valid_now  # noqa: E402
from extract import LLM, fill, prompt_text  # noqa: E402
from validate import ITEM_RE, TAG_RE, split_frontmatter  # noqa: E402

MAX_LINES = 400
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["pairs"], "properties": {"pairs": {
    "type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["a", "b", "kind", "why"],
        "properties": {"a": {"type": "string"}, "b": {"type": "string"},
                       "kind": {"type": "string", "enum": ["contradiction", "duplicate"]}, "why": {"type": "string"}}}}}}


def live_lines(vault, today):
    """[(id, file, text)] for every live [stated] line, outside Tensions and Archive."""
    out = []
    for p in sorted(Path(vault).rglob("*.md")):
        rel = p.relative_to(vault).as_posix()
        if rel.split("/")[0] in ("inbox", "data", "sessions"):
            continue
        parts = split_frontmatter(p.read_text(encoding="utf-8"))
        if not parts:
            continue
        top = sub = ""
        for line in parts[1]:
            if line.lstrip().startswith("#"):
                h = line.strip().lstrip("#").strip().lower()
                top, sub = (top, h) if line.lstrip().startswith("##") else (h, "")
                continue
            m = ITEM_RE.match(line)
            if "archive" in top or "tension" in sub or not m or not m.group(1).startswith("[stated]") or not valid_now(m.group(1), today):
                continue
            out.append((f"L{len(out) + 1}", rel, TAG_RE.sub("", m.group(1), count=1).strip()))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--base", default=os.environ.get("SOULME_LLM_BASE", "http://localhost:11434/v1"))
    ap.add_argument("--model", default=os.environ.get("SOULME_LLM_MODEL"))
    ap.add_argument("--key", default=os.environ.get("SOULME_LLM_KEY"))
    ap.add_argument("--today")
    a = ap.parse_args()
    if not a.model:
        sys.exit("set --model or SOULME_LLM_MODEL")
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    lines = live_lines(a.vault, today)
    if len(lines) > MAX_LINES:
        print(f"warning: {len(lines)} lines; only the first {MAX_LINES} are checked", file=sys.stderr)
        lines = lines[:MAX_LINES]
    by_id = {i: (f, t) for i, f, t in lines}
    got = LLM(a.base, a.model, a.key).json(fill(prompt_text("curate-conflicts.md"),
                                                lines="\n".join(f"{i} | {f} | {t}" for i, f, t in lines)),
                                           SCHEMA, "conflicts")
    if got is None:
        sys.exit("the model did not return valid JSON")
    seen, rows, dropped = set(), [], 0
    for pair in got.get("pairs") or []:
        a_, b_ = str(pair.get("a", "")).strip(), str(pair.get("b", "")).strip()
        key = tuple(sorted((a_, b_)))
        if a_ not in by_id or b_ not in by_id or a_ == b_ or key in seen:
            dropped += 1
            continue
        seen.add(key)
        (fa, ta), (fb, tb) = by_id[a_], by_id[b_]
        why = re.sub(r"\s+", " ", str(pair.get("why", ""))).strip()
        rows.append(f"- **{pair.get('kind', 'contradiction')}**: {why}\n  `{fa}`: {ta}\n  `{fb}`: {tb}")
    print("## Contradictions and duplicates (your model's judgement; you decide)")
    print("\n".join(rows) if rows else "- none")
    print(f"checked {len(lines)} lines, {len(rows)} pairs reported, {dropped} dropped (unknown ids or repeats)", file=sys.stderr)


if __name__ == "__main__":
    main()
