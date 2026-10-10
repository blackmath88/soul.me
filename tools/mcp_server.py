#!/usr/bin/env python3
"""MCP server (v4, optional layer, D-013): the vault as tools for any MCP client. Standard library + PyYAML.

Usage: python tools/mcp_server.py <vault> --profile work|personal [--client NAME] [--read-only]

Speaks MCP over stdio (one JSON-RPC message per line). Same rules as tools/export.py:
  - only [stated] lines inside their validity window, never `# Archive`, never inbox/, data/ or sessions/
  - the profile decides which files exist for this client (D-022); one server process per client
Tools: get_core, search (SQLite FTS5, rebuilt from the files, throwaway, D-005), list, read, get_skill,
last_handoff (personal only), propose (writes to inbox/ only, never to live files; off with --read-only).
Example client config (Claude Desktop, Claude Code, …):
  {"command": "python", "args": ["/path/soul.me/tools/mcp_server.py", "/path/soul-vault/vault", "--profile", "personal",
   "--client", "claude-home"]}
"""
import argparse
import datetime
import json
import re
import sqlite3
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export import DEFAULT, PROFILES, file_profiles, valid_now  # noqa: E402
from validate import ITEM_RE, NAME_RE, TAG_RE, split_frontmatter  # noqa: E402

PROTOCOL = "2025-06-18"
MAX_PROPOSE = 12
MAX_LINE = 300


class Vault:
    def __init__(self, root, profile, client, read_only, today=None):
        self.root, self.profile, self.client, self.read_only = Path(root), profile, client, read_only
        self.today = today or datetime.date.today()
        self.stamp, self.db = None, None

    # ---------- what this client may see ----------

    def files(self):
        """rel -> (frontmatter, served lines), for every live file this profile allows."""
        out = {}
        for p in sorted(self.root.rglob("*.md")):
            rel = p.relative_to(self.root).as_posix()
            top = rel.split("/")[0]
            if rel != "minime.md" and top not in DEFAULT:
                continue
            parts = split_frontmatter(p.read_text(encoding="utf-8"))
            if not parts:
                continue
            fm = yaml.safe_load(parts[0]) or {}
            if self.profile not in file_profiles(rel, fm):
                continue
            lines, top_heading = [], ""
            for line in parts[1]:
                if line.lstrip().startswith("#"):
                    if not line.lstrip().startswith("##"):
                        top_heading = line.strip().lstrip("#").strip().lower()
                    if "archive" not in top_heading:
                        lines.append(line.rstrip())
                    continue
                m = ITEM_RE.match(line)
                if not m or "archive" in top_heading:
                    continue
                tag = TAG_RE.match(m.group(1))
                if tag and tag.group(1) == "stated" and valid_now(m.group(1), self.today):
                    lines.append(line.rstrip())
            out[rel] = (fm, lines)
        return out

    def render(self, rel, fm, lines):
        desc = fm.get("description", "")
        return f"<!-- {rel} · {desc} -->\n" + "\n".join(lines).strip() + "\n"

    # ---------- the index (D-005: rebuilt from the files, never the source of truth) ----------

    def index(self):
        stamp = max((p.stat().st_mtime_ns for p in self.root.rglob("*.md")), default=0)
        if self.db is None or stamp != self.stamp:
            self.db = sqlite3.connect(":memory:")
            self.db.execute("CREATE VIRTUAL TABLE lines USING fts5(path UNINDEXED, heading, text, tokenize='unicode61')")
            for rel, (fm, lines) in self.files().items():
                heading = ""
                for line in lines:
                    if line.lstrip().startswith("#"):
                        heading = line.strip().lstrip("#").strip()
                        continue
                    text = TAG_RE.sub("", ITEM_RE.match(line).group(1), count=1).strip()
                    self.db.execute("INSERT INTO lines VALUES (?, ?, ?)", (rel, heading, text))
            self.stamp = stamp
        return self.db

    # ---------- tools ----------

    def get_core(self):
        fs = self.files()
        core = [r for r, (fm, _) in fs.items() if r == "minime.md" or str(fm.get("scope") or
                (fm.get("metadata") or {}).get("scope")) == "always"]
        return "\n".join(self.render(r, *fs[r]) for r in sorted(core, key=lambda r: r != "minime.md"))

    def search(self, query, limit=10):
        words = re.findall(r"\w+", query or "")
        if not words:
            return "empty query"
        q = " OR ".join('"' + w.replace('"', "") + '"' for w in words)
        rows = self.index().execute("SELECT path, heading, text FROM lines WHERE lines MATCH ? ORDER BY bm25(lines) LIMIT ?",
                                    (q, max(1, min(int(limit), 50)))).fetchall()
        return "\n".join(f"{p}{' · ' + h if h else ''}: {t}" for p, h, t in rows) or "no matches"

    def list(self, prefix=""):
        rows = [f"{r}: {fm.get('description', '')}" for r, (fm, _) in self.files().items() if r.startswith(prefix or "")]
        return "\n".join(rows) or "no files"

    def read(self, path):
        fs = self.files()
        if path not in fs:
            raise ValueError(f"{path}: no such file for this client (profile {self.profile})")
        return self.render(path, *fs[path])

    def get_skill(self, name):
        return self.read(f"skills/{name}/SKILL.md")

    def last_handoff(self):
        if self.profile != "personal":
            raise ValueError("sessions are never served in the work profile (D-022)")
        sessions = sorted((self.root / "sessions").glob("*.md"))
        if not sessions:
            return "no handoff yet"
        parts = split_frontmatter(sessions[-1].read_text(encoding="utf-8"))
        return f"<!-- sessions/{sessions[-1].name} -->\n" + "\n".join(l for l in parts[1] if l.strip()) + "\n"

    def propose(self, path, lines, told=False):
        """Writes to inbox/ only, as unreviewed lines. The person seals them; a tool never does (D-004, D-006)."""
        if self.read_only:
            raise ValueError("this server is read-only")
        allowed = {t for t, profiles in DEFAULT.items() if self.profile in profiles}
        top = path.split("/")[0]
        if ".." in path or (top not in allowed and path not in self.files()) or not (path == "minime.md" or re.fullmatch(
                r"(areas|people|topics)/[a-z0-9-]+\.md|skills/[a-z0-9-]+/SKILL\.md", path)):
            raise ValueError(f"{path}: not a live file this client may propose to (profile {self.profile})")
        if not isinstance(lines, list) or not lines:
            raise ValueError("lines must be a non-empty list of strings")
        tag = f"imported:{self.client}" if told else "inferred"
        clean = [re.sub(r"\s+", " ", str(l).replace("[", "(").replace("]", ")")).strip()[:MAX_LINE] for l in lines]
        clean = [l for l in clean if l][:MAX_PROPOSE]
        name = f"{self.today.isoformat()}-mcp-{self.client}"
        p = self.root / "inbox" / f"{name}.md"
        p.parent.mkdir(exist_ok=True)
        text = p.read_text(encoding="utf-8") if p.exists() else (
            f"---\nname: {name}\ndescription: proposals from the MCP client {self.client}, awaiting review\n"
            f"scope: global\nupdated: {self.today.isoformat()}\n---\n")
        new = [l for l in clean if f"] {l}\n" not in text]
        if new:
            text = text.rstrip("\n") + f"\n## → {path}\n" + "".join(f"- [{tag}] {l}\n" for l in new)
            p.write_text(text, encoding="utf-8")
        return f"{len(new)} line(s) waiting in inbox/{p.name} for the person to review; nothing in the live vault changed"


TOOLS = [
    ("get_core", "The person's core: minime.md (identity and how to work with them) plus files marked scope: always. "
     "Read this first.", {}),
    ("search", "Full-text search over the person's confirmed facts. Returns matching lines with their file.",
     {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}, ["query"]),
    ("list", "List the files this client may read, with descriptions.", {"prefix": {"type": "string"}}),
    ("read", "Read one file, e.g. areas/some-project.md.", {"path": {"type": "string"}}, ["path"]),
    ("get_skill", "Read one of the person's procedures by name.", {"name": {"type": "string"}}, ["name"]),
    ("last_handoff", "The most recent session handoff note (personal profile only).", {}),
    ("propose", "Suggest new facts for the person to review. Lines land in their inbox, never in the live vault. "
     "Set told=true only for things the person said in this conversation; leave it false for your own conclusions.",
     {"path": {"type": "string", "description": "target live file, e.g. minime.md or topics/tools.md"},
      "lines": {"type": "array", "items": {"type": "string"}, "maxItems": MAX_PROPOSE},
      "told": {"type": "boolean", "default": False}}, ["path", "lines"]),
]


def tool_list(vault):
    out = []
    for name, desc, props, *req in TOOLS:
        if name == "propose" and vault.read_only or name == "last_handoff" and vault.profile != "personal":
            continue
        out.append({"name": name, "description": desc,
                    "inputSchema": {"type": "object", "properties": props, "required": req[0] if req else []}})
    return out


def handle(vault, msg):
    method, params, mid = msg.get("method"), msg.get("params") or {}, msg.get("id")
    if mid is None:                                     # notification: no reply
        return None
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion") or PROTOCOL, "capabilities": {"tools": {}},
                  "serverInfo": {"name": "soul.me", "version": "0.1"},
                  "instructions": "The person's own, confirmed context. Call get_core first. Facts change only "
                                  "through the person: use propose for anything new."}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": tool_list(vault)}
    elif method == "tools/call":
        name, args = params.get("name"), params.get("arguments") or {}
        if name not in {t["name"] for t in tool_list(vault)}:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": f"unknown tool {name}"}}
        try:
            text, err = getattr(vault, name)(**args), False
        except (TypeError, ValueError) as e:
            text, err = str(e), True
        result = {"content": [{"type": "text", "text": text}], "isError": err}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vault")
    ap.add_argument("--profile", required=True, choices=PROFILES)
    ap.add_argument("--client", default="mcp", help="names this client in proposals: <provider>-<place> (D-020)")
    ap.add_argument("--read-only", action="store_true", help="no propose tool")
    ap.add_argument("--today", help="YYYY-MM-DD, for validity windows (default: today)")
    a = ap.parse_args()
    if not NAME_RE.match(a.client):
        sys.exit("--client must be lowercase letters, digits and hyphens, e.g. claude-home")
    today = datetime.date.fromisoformat(a.today) if a.today else None
    vault = Vault(a.vault, a.profile, a.client, a.read_only, today)
    for raw in sys.stdin:
        if not raw.strip():
            continue
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}
        else:
            reply = handle(vault, msg)
        if reply:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
