#!/usr/bin/env python3
"""A dumb, deterministic stand-in for an OpenAI-compatible model, for testing the intake plumbing.

  python tests/stub_llm.py [port]      # default 8765; then --base http://127.0.0.1:8765/v1 --model stub

It is not intelligent: the map step picks sentences by keyword and quotes them exactly, plus one
invented quote per call (which the pipeline must reject); the judge marks health words as sensitive.
Real quality numbers come from running tools/eval_extract.py against your own model.
"""
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

KEYWORDS = {"how-i-work": ["short", "english", "recommendation"], "what-i-learned": ["learned", "realised"],
            "what-i-built": ["shipped"], "career": ["want to move"], "procedures": ["usually", "always prepare"],
            "admin": ["renew", "running"]}
SENSITIVE = ["physio", "knee", "health"]


def answer(prompt):
    task = re.search(r"^TASK: (\w+)", prompt, re.M).group(1)
    if task == "map":
        lens = re.search(r"^Lens: (\S+)", prompt, re.M).group(1)
        chunk = prompt.split("<<<\n", 1)[1].rsplit("\n>>>", 1)[0]
        out = []
        for line in chunk.split("\n"):
            m = re.match(r"\[(m\d+) \| [\d-]+\] (.*)", line)
            if not m:
                continue
            for sent in re.split(r"(?<=[.!?])\s+", m.group(2)):
                if any(k in sent.lower() for k in KEYWORDS.get(lens, [])):
                    quote = " ".join(sent.split()[:25])
                    out.append({"claim": sent, "kind": "told", "quote": quote, "message_id": m.group(1),
                                "valid_from": None, "valid_to": None})
        out.append({"claim": "Invented fact", "kind": "concluded", "quote": "this sentence appears nowhere in the messages",
                    "message_id": "m1", "valid_from": None, "valid_to": None})
        return {"findings": out}
    if task == "judge":
        start = prompt.index("[", prompt.index("Candidates"))
        cands, _ = json.JSONDecoder().raw_decode(prompt[start:])
        return {"items": [{"id": c["id"], "keep": True, "confidence": 0.8, "stability": "months",
                           "sensitive": any(w in c["claim"].lower() for w in SENSITIVE), "target": c["target"],
                           "contradicts": None, "line": c["claim"]} for c in cands]}
    if task == "conflicts":                 # near-identical lines are duplicates; plus two ids that must be dropped
        rows = re.findall(r"^(L\d+) \| \S+ \| (.*)$", prompt, re.M)
        words = {i: set(re.findall(r"\w+", t.lower())) for i, t in rows}
        pairs = [{"a": a, "b": b, "kind": "duplicate", "why": "same fact twice"}
                 for k, (a, _) in enumerate(rows) for b, _ in rows[k + 1:]
                 if len(words[a] & words[b]) / len(words[a] | words[b]) >= 0.7]
        return {"pairs": pairs + [{"a": "L999", "b": "L1", "kind": "contradiction", "why": "invented"},
                                  {"a": "L1", "b": "L1", "kind": "duplicate", "why": "self"}]}
    return {"gaps": ["What would Mara like assistants to stop doing?", "Which work does Mara want less of?"]}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        content = json.dumps(answer(body["messages"][-1]["content"]))
        data = json.dumps({"choices": [{"message": {"role": "assistant", "content": content}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8765), Handler).serve_forever()
