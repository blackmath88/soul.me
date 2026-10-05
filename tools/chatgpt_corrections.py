#!/usr/bin/env python3
"""Pull short replies that follow an assistant answer out of a ChatGPT export: the raw material for corrections.

Usage: python tools/chatgpt_corrections.py <export_dir> <out_file.jsonl>

Same allowlist (D-029), active branch and in-repo refusal as tools/chatgpt_export.py. One JSON line per user
turn that directly follows an assistant turn and is at most 300 chars:
  {conv_id, date, title, user, prev_assistant (≤300 chars), hint}
`hint` is true when the turn contains a correction-ish keyword. It is a hint only: nothing is filtered on it,
and there is no model in this script. prompts/classify-corrections.md does the judging, on your machine.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chatgpt_export import read_asset_names, read_conversations, refuse_repo_output, turns  # noqa: E402

MAX_USER = 300
MAX_PREV = 300
HINTS = ["kürzer", "länger", "nicht", "nochmal", "stattdessen", "bitte ohne",
         "shorter", "don't", "don’t", "instead", "again", "keep the"]
HINT_RE = re.compile("|".join(r"(?<!\w)" + re.escape(h) + r"(?!\w)" for h in HINTS), re.I)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    export_dir, out_file = Path(sys.argv[1]), Path(sys.argv[2])
    refuse_repo_output(out_file)
    names = read_asset_names(export_dir)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    n = hinted = 0
    with out_file.open("w", encoding="utf-8") as f:
        for conv in read_conversations(export_dir):
            ts = turns(conv, names)
            for prev, cur in zip(ts, ts[1:]):
                if prev["role"] != "assistant" or cur["role"] != "user" or cur["pasted"]:
                    continue
                if len(cur["text"]) > MAX_USER:
                    continue
                hint = bool(HINT_RE.search(cur["text"]))
                f.write(json.dumps({
                    "conv_id": str(conv.get("id") or conv.get("conversation_id") or ""),
                    "date": cur["when"].strftime("%Y-%m-%d") if cur["when"] else None,
                    "title": conv.get("title") or "",
                    "user": cur["text"],
                    "prev_assistant": prev["text"][:MAX_PREV],
                    "hint": hint}, ensure_ascii=False) + "\n")
                n += 1
                hinted += hint
    print(f"{n} short follow-up turns written to {out_file} ({hinted} with a correction hint)")


if __name__ == "__main__":
    main()
