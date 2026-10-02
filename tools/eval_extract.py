#!/usr/bin/env python3
"""Score a model on the fictional fixtures before any real data goes through it.

  python tools/eval_extract.py --base http://localhost:11434/v1 --model qwen2.5:14b

Runs the full intake pipeline (tools/extract.py) on tests/fixtures (a ChatGPT-shaped export as a ZIP and
a Claude-shaped export) against a temporary copy of the fictional vault, then reports:
  - calls        schema-valid answers / model calls
  - quotes       findings whose quote was found word for word / all findings
  - recall       expected findings (tests/fixtures/gold.json) among the kept findings, and in the inbox top N
  - leaks        trap strings (IBAN, AHV, email, phone, client name, health) in the inbox or report: must be 0
  - valid        the written inbox files pass tools/validate.py
Exit code 1 if anything leaks or the inbox is invalid.
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402
import validate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=os.environ.get("SOULME_LLM_BASE", "http://localhost:11434/v1"))
    ap.add_argument("--model", default=os.environ.get("SOULME_LLM_MODEL"))
    ap.add_argument("--top", type=int, default=12)
    a = ap.parse_args()
    if not a.model:
        sys.exit("set --model or SOULME_LLM_MODEL")
    gold = json.loads((FIX / "gold.json").read_text())
    deny = (FIX / "denylist.txt").read_text().split()
    tmp = Path(tempfile.mkdtemp(prefix="soulme-eval-"))
    try:
        vault = tmp / "vault"
        shutil.copytree(ROOT / "vault", vault)
        for p in (vault / "inbox").glob("*.md"):
            p.unlink()
        zpath = tmp / "chatgpt-export.zip"
        with zipfile.ZipFile(zpath, "w") as z:
            z.write(FIX / "chatgpt-conversations.json", "conversations.json")
        llm = extract.LLM(a.base, a.model, os.environ.get("SOULME_LLM_KEY"))
        kept, texts, counts = [], [], {"findings_raw": 0, "verified": 0}
        for src, source in ((zpath, "chatgpt-home"), (FIX / "claude-conversations.json", "claude-home")):
            report, _ = extract.run(src, source, vault, llm, a.top, extract.PROMPTS / "lenses.md", deny,
                                    state_path=None, today="2026-10-01", log=lambda *_: None)
            md = extract.inbox_markdown(report, source, a.top)
            (vault / "inbox" / f"2026-10-01-{source}.md").write_text(md, encoding="utf-8")
            texts += [md, json.dumps(report, ensure_ascii=False)]
            kept += [(f, i < a.top) for i, f in enumerate(report["findings"])]
            for k in counts:
                counts[k] += report["counts"][k]
        _, errors = validate.validate(vault)

        def hit(e, f):
            text = (f.get("line", "") + " " + f["claim"]).lower()
            return all(w in text for w in e["all"])
        found = [e for e in gold["expect"] if any(hit(e, f) for f, _ in kept)]
        in_top = [e for e in gold["expect"] if any(hit(e, f) for f, top in kept if top)]
        leaks = sorted({t for t in gold["traps"] for s in texts if t.lower() in s.lower()})

        n = len(gold["expect"])
        print(f"model   {a.model} @ {a.base}")
        print(f"calls   {llm.calls - llm.failed}/{llm.calls} schema-valid")
        print(f"quotes  {counts['verified']}/{counts['findings_raw']} verified word for word")
        print(f"recall  {len(found)}/{n} kept · {len(in_top)}/{n} in inbox top {a.top}")
        missing = [e['lens'] + ': ' + ' + '.join(e['all']) for e in gold['expect'] if e not in found]
        if missing:
            print("        missing: " + "; ".join(missing))
        print(f"leaks   {len(leaks)}" + (f"  ({', '.join(leaks)})" if leaks else ""))
        print(f"valid   {'yes' if not errors else 'NO: ' + '; '.join(errors[:3])}")
        sys.exit(1 if leaks or errors else 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
