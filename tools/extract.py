#!/usr/bin/env python3
"""Automated intake: chat exports and notes -> a short, ranked inbox file for the person to seal.

Usage:
  python tools/extract.py <export.zip | conversations.json | note.md> --source chatgpt-home [options]

Runs on your machine against any OpenAI-compatible endpoint (Ollama, LM Studio, llama.cpp, vLLM):
  --base  (or SOULME_LLM_BASE, default http://localhost:11434/v1)
  --model (or SOULME_LLM_MODEL)

Stages: parse (only the person's own messages, only new ones) -> redact (code, before any model)
-> map (each chunk x each lens, JSON with quotes) -> verify quotes -> merge + compare with the vault
-> judge -> gaps for the next run -> write inbox/<date>-<source>.md (top N) and data/reports/<...>.json.
Nothing is ever written to live vault files: sealing stays with the person (D-006, review option A).
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
CHUNK_CHARS = 6000
STOP = set("the a an and or of to in on for with is are was were be been it its this that as at by from not no "
           "they them their he she his her you your i me my we our very more most also than then".split())

# ---------- 1 parse: only the person's own messages ----------

def _chatgpt(conv):
    """Walk the active branch (current_node -> root) and keep user turns."""
    mapping, node, out = conv.get("mapping") or {}, conv.get("current_node"), []
    while node and node in mapping:
        msg = mapping[node].get("message") or {}
        if (msg.get("author") or {}).get("role") == "user":
            parts = (msg.get("content") or {}).get("parts") or []
            text = "\n".join(p for p in parts if isinstance(p, str)).strip()
            ts = msg.get("create_time") or conv.get("create_time")
            if text:
                out.append((ts, text))
        node = mapping[node].get("parent")
    return list(reversed(out))


def _claude(conv):
    out = []
    for m in conv.get("chat_messages") or []:
        if m.get("sender") != "human":
            continue
        text = (m.get("text") or "").strip() or "\n".join(
            c.get("text", "") for c in m.get("content") or [] if c.get("type") == "text").strip()
        if text:
            out.append((m.get("created_at"), text))
    return out


def _stamp(ts):
    """ISO timestamp (sortable) from epoch seconds or an ISO string."""
    if isinstance(ts, (int, float)):
        return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    if isinstance(ts, str) and re.match(r"\d{4}-\d{2}-\d{2}", ts):
        return (ts[:19] if "T" in ts else ts[:10] + "T00:00:00")
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def load_messages(path):
    """Return [{id, conv, title, date, text}] for everything the person wrote."""
    path = Path(path)
    if path.suffix in (".md", ".txt"):
        text = path.read_text(encoding="utf-8")
        ts = _stamp(path.stat().st_mtime)
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        return [{"id": f"m{i+1}", "conv": path.stem, "title": path.stem, "ts": ts, "date": ts[:10], "text": p}
                for i, p in enumerate(paras)]
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.endswith("conversations.json"))
            data = json.loads(z.read(name))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    msgs = []
    for conv in data:
        turns = _chatgpt(conv) if "mapping" in conv else _claude(conv)
        cid = conv.get("id") or conv.get("conversation_id") or conv.get("uuid") or conv.get("title", "")
        title = conv.get("title") or conv.get("name") or ""
        for ts, text in turns:
            st = _stamp(ts)
            msgs.append({"id": f"m{len(msgs)+1}", "conv": str(cid), "title": title, "ts": st, "date": st[:10], "text": text})
    return msgs

# ---------- 2 redact: code, before any model sees the text (D-024) ----------

REDACT = [
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("ahv", re.compile(r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b")),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b")),
    ("card", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("phone", re.compile(r"(?:\+|\b0)\d[\d\s/().-]{7,}\d")),
]


def redact(msgs, denylist):
    counts = {}
    deny = [re.compile(r"\b" + re.escape(t) + r"\b", re.I) for t in denylist if t]
    for m in msgs:
        t = m["text"]
        for kind, rx in REDACT + [("denylist", d) for d in deny]:
            t, n = rx.subn(f"<redacted:{kind}>", t)
            if n:
                counts[kind] = counts.get(kind, 0) + n
        m["text"] = t
    return counts


def chunks(msgs):
    out, cur, size = [], [], 0
    for m in msgs:
        line = f"[{m['id']} | {m['date']}] {m['text'][:CHUNK_CHARS]}"
        if cur and size + len(line) > CHUNK_CHARS:
            out.append(cur)
            cur, size = [], 0
        cur.append((m, line))
        size += len(line)
    if cur:
        out.append(cur)
    return out

# ---------- the vault as context ----------

TAG_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\[(stated|inferred|imported:[a-z0-9_-]+)\]\s*(?:\((?:valid_from|valid_to):[^)]*\)\s*)*(.*)$")


def vault_lines(vault):
    """Live lines as (file, text); inbox and data excluded."""
    out = []
    for p in sorted(Path(vault).rglob("*.md")):
        rel = p.relative_to(vault).as_posix()
        if rel.startswith(("inbox/", "data/")):
            continue
        for line in p.read_text(encoding="utf-8").split("\n"):
            m = TAG_RE.match(line)
            if m and m.group(1) == "stated":
                out.append((rel, m.group(2).strip()))
    return out


def pending_lines(vault):
    """Lines already waiting in inbox/, so a new run doesn't propose them again."""
    out = []
    for p in sorted((Path(vault) / "inbox").glob("*.md")):
        for line in p.read_text(encoding="utf-8").split("\n"):
            m = TAG_RE.match(line)
            if m:
                out.append(re.sub(r'\s*\(quote: "[^"]*"\)', "", m.group(2)).strip())
    return out


def vault_context(lines, target=None, limit=3000):
    pick = [l for l in lines if l[0] == "minime.md" or (target and l[0].startswith(target.split("#")[0].rstrip("/")))]
    text = "\n".join(f"- ({f}) {t}" for f, t in pick)
    return text[:limit] or "(empty)"

# ---------- the model ----------

def prompt_text(name):
    s = (PROMPTS / name).read_text(encoding="utf-8")
    m = re.search(r"```text\n(.*?)```", s, re.S)
    return m.group(1) if m else s


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace("{" + k + "}", v)
    return tpl


class LLM:
    def __init__(self, base, model, key=None):
        self.base, self.model, self.key = base.rstrip("/"), model, key
        self.calls = self.failed = 0

    def _post(self, body):
        req = urllib.request.Request(self.base + "/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              **({"Authorization": "Bearer " + self.key} if self.key else {})})
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]

    def json(self, prompt, schema, name):
        """Ask for schema-constrained JSON; fall back to json_object, then to plain text + parse."""
        self.calls += 1
        msgs = [{"role": "user", "content": prompt}]
        formats = [{"type": "json_schema", "json_schema": {"name": name, "schema": schema, "strict": True}},
                   {"type": "json_object"}, None]
        for fmt in formats:
            body = {"model": self.model, "messages": msgs, "temperature": 0}
            if fmt:
                body["response_format"] = fmt
            try:
                text = self._post(body)
            except urllib.error.HTTPError as e:
                if e.code in (400, 404, 422) and fmt:
                    continue
                raise
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                msgs = msgs + [{"role": "assistant", "content": text},
                               {"role": "user", "content": "That was not valid JSON. Return only the JSON object."}]
        self.failed += 1
        return None


NULLABLE = {"type": ["string", "null"]}
MAP_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["findings"], "properties": {"findings": {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
        "required": ["claim", "kind", "quote", "message_id", "valid_from", "valid_to"],
        "properties": {"claim": {"type": "string"}, "kind": {"type": "string", "enum": ["told", "pattern", "concluded"]},
                       "quote": {"type": "string"}, "message_id": {"type": "string"},
                       "valid_from": NULLABLE, "valid_to": NULLABLE}}}}}
JUDGE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["items"], "properties": {"items": {
    "type": "array", "items": {"type": "object", "additionalProperties": False,
        "required": ["id", "keep", "confidence", "stability", "sensitive", "target", "contradicts", "line"],
        "properties": {"id": {"type": "string"}, "keep": {"type": "boolean"}, "confidence": {"type": "number"},
                       "stability": {"type": "string", "enum": ["months", "weeks", "unclear"]},
                       "sensitive": {"type": "boolean"}, "target": {"type": "string"},
                       "contradicts": NULLABLE, "line": {"type": "string"}}}}}}
GAPS_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["gaps"],
               "properties": {"gaps": {"type": "array", "items": {"type": "string"}}}}

# ---------- 3-5 map, verify, merge, compare ----------

def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[\"'`’‘“”]", "", s.lower())).strip()


def tokens(s):
    return {w for w in re.findall(r"[a-zäöüéèàß0-9]+", s.lower()) if len(w) > 2 and w not in STOP}


def jaccard(a, b):
    a, b = tokens(a), tokens(b)
    return len(a & b) / len(a | b) if a and b else 0.0


def verify(f, chunk):
    """The quote must appear word for word in the cited message (or, failing that, the same chunk)."""
    q = norm(f.get("quote", ""))
    if len(q.split()) < 3:
        return None
    by_id = {m["id"]: m for m, _ in chunk}
    order = [by_id[f["message_id"]]] if f.get("message_id") in by_id else []
    for m in order + [m for m, _ in chunk]:
        if q in norm(m["text"]):
            return m
    return None


def merge(found):
    groups = []
    for f in found:
        for g in groups:
            if jaccard(g["claim"], f["claim"]) >= 0.6:
                g["evidence"].append(f["evidence"][0])
                break
        else:
            groups.append(f)
    for g in groups:
        g["recurrence"] = len({e["conversation"] for e in g["evidence"]})
        g["months"] = len({e["date"][:7] for e in g["evidence"]})
    return groups


def score(f):
    stab = {"months": 1.0, "unclear": .8, "weeks": .5}.get(f.get("stability"), .8)
    kind = {"told": 1.0, "pattern": 1.0, "concluded": .8}[f["kind"]]
    return round(f.get("confidence", 0) * stab * kind * (.6 + .4 * min(1, (f["recurrence"] - 1) / 2)), 3)

# ---------- the run ----------

def load_lenses(path):
    lenses = []
    for block in re.split(r"^## ", Path(path).read_text(encoding="utf-8"), flags=re.M)[1:]:
        lid = block.split("\n", 1)[0].strip()
        t = re.search(r"^target:\s*(.+)$", block, re.M)
        q = re.search(r"^question:\s*(.+)$", block, re.M)
        if t and q:
            lenses.append({"id": lid, "target": t.group(1).strip(), "question": q.group(1).strip()})
    return lenses


def run(src, source, vault, llm, top=12, lenses_path=PROMPTS / "lenses.md", denylist=(), state_path=None,
        since=None, today=None, log=print):
    today = today or datetime.date.today().isoformat()
    state = json.loads(Path(state_path).read_text()) if state_path and Path(state_path).exists() else {}
    last = since or state.get("last", {}).get(source)
    msgs = [m for m in load_messages(src) if not last or m["ts"] > last]
    redactions = redact(msgs, denylist)
    lenses = load_lenses(lenses_path)
    lines = vault_lines(vault)
    gaps = state.get("gaps", [])
    parts = chunks(msgs)
    log(f"{len(msgs)} new messages, {len(parts)} chunks, {len(lenses)} lenses, redacted {redactions or 'nothing'}")

    found, raw, bad_quote = [], 0, 0
    tpl = prompt_text("intake-map.md")
    for ci, chunk in enumerate(parts):
        text = "\n".join(line for _, line in chunk)
        for lens in lenses:
            out = llm.json(fill(tpl, lens=lens["id"], question=lens["question"],
                                vault=vault_context(lines, lens["target"]),
                                gaps="\n".join("- " + g for g in gaps) or "(none)", chunk=text), MAP_SCHEMA, "findings")
            for f in (out or {}).get("findings", []):
                raw += 1
                m = verify(f, chunk) if isinstance(f, dict) and f.get("claim") else None
                if not m:
                    bad_quote += 1
                    continue
                ok = lambda v: v if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}", v) else None
                found.append({"lens": lens["id"], "target": lens["target"], "claim": f["claim"].strip(),
                              "kind": f.get("kind") if f.get("kind") in ("told", "pattern", "concluded") else "concluded",
                              "valid_from": ok(f.get("valid_from")), "valid_to": ok(f.get("valid_to")),
                              # no conversation titles: vendors write them from the content, so they can leak
                              "evidence": [{"conversation": m["conv"], "date": m["date"],
                                            "quote": f["quote"].strip()}]})
        log(f"  chunk {ci+1}/{len(parts)}: {len(found)} verified so far")

    merged = merge(found)
    known = [t for _, t in lines] + pending_lines(vault)
    fresh = []
    for f in merged:
        if max((jaccard(f["claim"], t) for t in known), default=0) < 0.7:
            fresh.append(f)
    for i, f in enumerate(fresh):
        f["id"] = f"f{i+1}"

    judged = {}
    jt = prompt_text("intake-judge.md")
    for k in range(0, len(fresh), 20):
        batch = [{"id": f["id"], "claim": f["claim"], "kind": f["kind"], "lens": f["lens"], "target": f["target"],
                  "recurrence": f["recurrence"], "quote": f["evidence"][0]["quote"]} for f in fresh[k:k + 20]]
        out = llm.json(fill(jt, vault=vault_context(lines, None, 4000), candidates=json.dumps(batch, ensure_ascii=False, indent=1)),
                       JUDGE_SCHEMA, "judgement")
        for it in (out or {}).get("items", []):
            if isinstance(it, dict) and "id" in it:
                judged[it["id"]] = it
    kept = []
    for f in fresh:
        j = judged.get(f["id"])
        if not j or not j.get("keep") or j.get("sensitive"):
            continue
        f.update(confidence=min(1.0, max(0.0, float(j.get("confidence") or 0))), stability=j.get("stability"),
                 target=j.get("target") or f["target"], contradicts=j.get("contradicts"), line=j.get("line") or f["claim"])
        f["score"] = score(f)
        kept.append(f)
    kept.sort(key=lambda f: -f["score"])

    new_gaps = (llm.json(fill(prompt_text("intake-gaps.md"),
                              lenses="\n".join(f"- {l['id']}: {l['question']}" for l in lenses),
                              vault=vault_context(lines, None, 4000),
                              findings="\n".join("- " + f["line"] for f in kept[:30]) or "(nothing new)"),
                         GAPS_SCHEMA, "gaps") or {}).get("gaps", [])[:3]

    report = {"source": source, "date": today, "model": llm.model,
              "counts": {"messages": len(msgs), "chunks": len(parts), "calls": llm.calls, "failed_calls": llm.failed,
                         "redactions": redactions, "findings_raw": raw, "quote_failed": bad_quote,
                         "verified": len(found), "merged": len(merged), "already_known": len(merged) - len(fresh),
                         "kept": len(kept), "in_inbox": min(top, len(kept))},
              "gaps": new_gaps, "findings": kept}
    newest = max((m["ts"] for m in msgs), default=last)
    state.setdefault("last", {})[source] = newest
    state["gaps"] = new_gaps or gaps
    return report, state


def inbox_markdown(report, source, top, name=None):
    """The digest: top N findings, grouped by target, each with its quote. Passes tools/validate.py."""
    def clean(s):
        return re.sub(r"\s+", " ", s.replace('"', "'").replace("[", "(").replace("]", ")")).strip()
    name = name or f"{report['date']}-{source}"
    rd = report["counts"]["redactions"]
    fm = [f"name: {name}",
          f"description: ranked findings from {source}, top {report['counts']['in_inbox']} of {report['counts']['kept']}; full report in {report.get('file', 'data/reports/')}",
          "scope: global", f"updated: {report['date']}", "dropped: " + json.dumps(rd),
          "questions: " + json.dumps([clean(g) for g in report.get("gaps", [])], ensure_ascii=False)]
    body, groups = [], {}
    for f in report["findings"][:top]:
        head = f"## → {f['target']}" + (" · contradicts the vault" if f.get("contradicts") else "")
        groups.setdefault(head, []).append(f)
    for head, items in groups.items():
        body.append(head)
        for f in items:
            tag = f"imported:{source}" if f["kind"] == "told" else "inferred"
            valid = "".join(f" ({k}: {f[k]})" for k in ("valid_from", "valid_to") if f.get(k))
            q = clean(f["evidence"][0]["quote"])
            body.append(f"- [{tag}]{valid} {clean(f['line'])} (quote: \"{q}\")")
    return "---\n" + "\n".join(fm) + "\n---\n" + "\n".join(body) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("--source", required=True, help="<provider>-<place>, e.g. chatgpt-home (D-020)")
    ap.add_argument("--vault", default="vault")
    ap.add_argument("--base", default=os.environ.get("SOULME_LLM_BASE", "http://localhost:11434/v1"))
    ap.add_argument("--model", default=os.environ.get("SOULME_LLM_MODEL"))
    ap.add_argument("--top", type=int, default=12, help="lines in the inbox digest (default 12)")
    ap.add_argument("--lenses", default=str(PROMPTS / "lenses.md"))
    ap.add_argument("--denylist", help="one term per line, e.g. client and employer names (default: <vault>/data/denylist.txt)")
    ap.add_argument("--since", help="only messages after YYYY-MM-DD (default: since the last run for this source)")
    a = ap.parse_args()
    if not a.model:
        sys.exit("set --model or SOULME_LLM_MODEL")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.source):
        sys.exit("--source must be lowercase <provider>-<place>, e.g. chatgpt-home")
    vault = Path(a.vault)
    data = vault / "data"
    dl = Path(a.denylist) if a.denylist else data / "denylist.txt"
    deny = [t.strip() for t in dl.read_text(encoding="utf-8").splitlines() if t.strip()] if dl.exists() else []
    llm = LLM(a.base, a.model, os.environ.get("SOULME_LLM_KEY"))
    report, state = run(a.input, a.source, vault, llm, a.top, a.lenses, deny, data / ".intake-state.json", a.since)
    (data / "reports").mkdir(parents=True, exist_ok=True)
    rp = data / "reports" / f"{datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')}-{a.source}.json"
    report["file"] = "data/reports/" + rp.name
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (data / ".intake-state.json").write_text(json.dumps(state, indent=1), encoding="utf-8")
    c = report["counts"]
    if c["in_inbox"]:
        ip, k = vault / "inbox" / f"{report['date']}-{a.source}.md", 1
        while ip.exists():                      # never overwrite lines still waiting for review
            k += 1
            ip = vault / "inbox" / f"{report['date']}-{a.source}-{k}.md"
        ip.parent.mkdir(exist_ok=True)
        ip.write_text(inbox_markdown(report, a.source, a.top, ip.stem), encoding="utf-8")
        print(f"inbox: {ip} ({c['in_inbox']} lines)  report: {rp}")
    else:
        print(f"nothing new for the inbox  report: {rp}")
    print(f"verified {c['verified']} of {c['findings_raw']} findings, merged to {c['merged']}, "
          f"{c['already_known']} already in the vault or inbox, kept {c['kept']}; failed calls {c['failed_calls']}")


if __name__ == "__main__":
    main()
