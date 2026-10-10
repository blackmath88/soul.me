#!/usr/bin/env python3
"""Classify corrections (v1, automated): JSONL from tools/chatgpt_corrections.py -> one inbox file of
Operating-manual candidates with (seen: n), using your own model.

Usage: python tools/classify_corrections.py <corrections.jsonl> --vault <vault> [--batch 100] [--source chatgpt-home]
                                            [--stage] [--base URL] [--model NAME]

Runs locally like tools/extract.py (same --base/--model and SOULME_LLM_* variables). Before any model sees a line,
IDs, emails, phones and the terms in <vault>/data/denylist.txt are redacted in code (D-024). The model labels
lines and proposes candidates by line id (prompts/intake-corrections.md); code drops unknown ids, counts `seen` as
distinct conversations, and merges batches. Writes inbox/<date>-<source>-corrections.md, or data/staged/ with --stage
(D-027). Never touches live files.
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import LLM, fill, prompt_text, redact  # noqa: E402

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["labels", "candidates"], "properties": {
    "labels": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["id", "label"],
               "properties": {"id": {"type": "string"},
                              "label": {"type": "string", "enum": ["preference", "one-off", "noise"]}}}},
    "candidates": {"type": "array", "items": {"type": "object", "additionalProperties": False,
                   "required": ["line", "ids", "same_as"],
                   "properties": {"line": {"type": "string"}, "ids": {"type": "array", "items": {"type": "string"}},
                                  "same_as": {"type": ["string", "null"]}}}}}}


def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("[", "(").replace("]", ")").replace('"', "'")).strip()[:200]


def classify(rows, llm, batch):
    """rows: [{id, conv, user, prev}] -> (candidates [{line, convs}], label counts, dropped ids)."""
    cands, labels, dropped = [], {"preference": 0, "one-off": 0, "noise": 0}, 0
    for start in range(0, len(rows), batch):
        part = rows[start:start + batch]
        by_id = {r["id"]: r for r in part}
        prev = "\n".join(f"P{i} | {c['line']}" for i, c in enumerate(cands, 1)) or "none"
        lines = "\n".join(f"{r['id']} | {r['user']} | {r['prev']}" for r in part)
        got = llm.json(fill(prompt_text("intake-corrections.md"), previous=prev, lines=lines), SCHEMA, "corrections")
        if got is None:
            print(f"batch {start // batch + 1}: no valid JSON, skipped", file=sys.stderr)
            continue
        for l in got.get("labels") or []:
            if l.get("id") in by_id and l.get("label") in labels:
                labels[l["label"]] += 1
        for c in got.get("candidates") or []:
            ids = [i for i in c.get("ids") or [] if i in by_id]
            dropped += len(c.get("ids") or []) - len(ids)
            line = clean(c.get("line", ""))
            if not ids or not line:
                continue
            convs = {by_id[i]["conv"] for i in ids}
            m = re.fullmatch(r"P(\d+)", str(c.get("same_as") or ""))
            if m and 1 <= int(m.group(1)) <= len(cands):
                cands[int(m.group(1)) - 1]["convs"] |= convs
            else:
                cands.append({"line": line, "convs": convs})
    return cands, labels, dropped


def markdown(name, source, cands, labels, batches):
    fm = [f"name: {name}",
          f"description: Operating-manual candidates from short corrections in the {source} export, {batches} batch(es)",
          "scope: global", f"updated: {name[:10]}",
          "labels: {" + ", ".join(f"{k}: {v}" for k, v in labels.items()) + "}"]
    body = ["## → minime.md: Operating manual"]
    body += [f"- [imported:{source}] (seen: {len(c['convs'])}) {c['line']}"
             for c in sorted(cands, key=lambda c: -len(c["convs"]))]
    return "---\n" + "\n".join(fm) + "\n---\n" + "\n".join(body) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jsonl")
    ap.add_argument("--vault", default="vault")
    ap.add_argument("--source", default="chatgpt-home", help="<provider>-<place> (D-020)")
    ap.add_argument("--batch", type=int, default=100, help="lines per model call (default 100)")
    ap.add_argument("--stage", action="store_true", help="write to data/staged/ for tools/release.py (D-027)")
    ap.add_argument("--base", default=os.environ.get("SOULME_LLM_BASE", "http://localhost:11434/v1"))
    ap.add_argument("--model", default=os.environ.get("SOULME_LLM_MODEL"))
    ap.add_argument("--today")
    a = ap.parse_args()
    if not a.model:
        sys.exit("set --model or SOULME_LLM_MODEL")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.source):
        sys.exit("--source must be lowercase <provider>-<place>, e.g. chatgpt-home")
    vault = Path(a.vault)
    rows = []
    for n, raw in enumerate(Path(a.jsonl).read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip():
            d = json.loads(raw)
            rows.append({"id": f"c{n}", "conv": d.get("conv_id") or f"unknown-{n}",
                         "text": d.get("user", ""), "prev": d.get("prev_assistant", "")})
    dl = vault / "data" / "denylist.txt"
    deny = [t.strip() for t in dl.read_text(encoding="utf-8").splitlines() if t.strip()] if dl.exists() else []
    counts = redact(rows, deny)                                  # user replies
    prev = [{"text": r["prev"]} for r in rows]
    for k, v in redact(prev, deny).items():                      # and the assistant context
        counts[k] = counts.get(k, 0) + v
    for r, p in zip(rows, prev):
        r["user"], r["prev"] = clean(r["text"]), clean(p["text"])[:300]

    cands, labels, dropped = classify(rows, LLM(a.base, a.model, os.environ.get("SOULME_LLM_KEY")), max(1, a.batch))
    batches = (len(rows) + a.batch - 1) // a.batch
    print(f"{len(rows)} lines in {batches} batch(es): {labels}; {len(cands)} candidates; {dropped} unknown ids dropped; "
          f"redacted {counts or 'nothing'}", file=sys.stderr)
    if not cands:
        print("no preferences found, nothing written")
        return
    today = a.today or datetime.date.today().isoformat()
    dest = vault / "data" / "staged" if a.stage else vault / "inbox"
    name, k = f"{today}-{a.source}-corrections", 2
    while (dest / f"{name}.md").exists() or (vault / "inbox" / f"{name}.md").exists():
        name, k = f"{today}-{a.source}-corrections-{k}", k + 1
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{name}.md").write_text(markdown(name, a.source, cands, labels, batches), encoding="utf-8")
    print(f"{'staged' if a.stage else 'inbox'}: {dest / (name + '.md')}")


if __name__ == "__main__":
    main()
